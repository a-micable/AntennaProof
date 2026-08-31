"""Verification Agent — rejects unsupported verdicts and routes workflow."""

from __future__ import annotations

from src.schemas import EvidenceItem, MetricStatus, OverallVerdict, ProposedReview
from src.state.workflow_state import VerifierAction, VerifierDecision


def _mandatory_keys(mandatory: list[str]) -> set[str]:
    keys: set[str] = set()
    for m in mandatory:
        keys.add("minimum_s11" if m in ("min_s11", "minimum_s11") else m)
    return keys


def _recompute_overall(results: list, mandatory: set[str]) -> OverallVerdict:
    rel = [r for r in results if r.metric in mandatory]
    if any(r.status == MetricStatus.FAIL for r in rel):
        return OverallVerdict.FAIL
    if any(r.status == MetricStatus.INSUFFICIENT_EVIDENCE for r in rel):
        return OverallVerdict.INSUFFICIENT_EVIDENCE
    return OverallVerdict.PASS


def _needs_notes_pass(has_notes: bool, phase: int, evidence: list[EvidenceItem], pg_status: MetricStatus | None) -> bool:
    if not has_notes or phase >= 3 or pg_status is None:
        return False
    has_json_gain = any(e.metric == "peak_gain" and e.source == "measurements.json" for e in evidence)
    has_note_gain = any(e.metric == "peak_gain_claimed" for e in evidence)
    # Retry notes only when gain verdict could change: missing json, IE, FAIL, or unchecked contradiction
    if pg_status == MetricStatus.PASS and has_json_gain:
        return False
    if has_note_gain:
        return False
    return pg_status in (MetricStatus.FAIL, MetricStatus.INSUFFICIENT_EVIDENCE) or not has_json_gain


def verify_review(
    proposed: ProposedReview,
    evidence: list[EvidenceItem],
    mandatory_metrics: list[str],
    *,
    extraction_phase: int = 1,
    max_phase: int = 3,
    has_s11: bool = False,
    has_notes: bool = False,
) -> VerifierDecision:
    violations: list[str] = []
    evidence_ids = {e.evidence_id for e in evidence}
    evidence_metrics = {e.metric for e in evidence}
    mandatory = _mandatory_keys(mandatory_metrics)

    missing_citable = False
    corrected_results = []

    for mr in proposed.metric_results:
        row = mr.model_copy()
        is_mandatory = mr.metric in mandatory

        if is_mandatory and mr.status in (MetricStatus.PASS, MetricStatus.FAIL):
            if mr.measured is None:
                violations.append(f"{mr.metric}: decision without measured value")
                row.status = MetricStatus.INSUFFICIENT_EVIDENCE
                row.reason = "Verifier: no measured value"
            elif not mr.evidence_id or mr.evidence_id not in evidence_ids:
                violations.append(f"{mr.metric}: missing or invalid evidence_id")
                missing_citable = True
                row.status = MetricStatus.INSUFFICIENT_EVIDENCE
                row.reason = "Verifier: PASS/FAIL requires traceable evidence_id"

        if mr.metric == "peak_gain" and mr.status == MetricStatus.PASS and "peak_gain" not in evidence_metrics:
            violations.append("peak_gain: PASS without peak_gain measurement")
            row.status = MetricStatus.INSUFFICIENT_EVIDENCE
            row.reason = "Verifier: directivity/notes alone cannot justify gain PASS"
            missing_citable = True

        corrected_results.append(row)

    overall = _recompute_overall(corrected_results, mandatory)
    corrected = proposed.model_copy(
        update={
            "metric_results": corrected_results,
            "overall_verdict": overall,
            "insufficient_evidence": [
                f"{r.metric}: {r.reason}" for r in corrected_results if r.status == MetricStatus.INSUFFICIENT_EVIDENCE
            ],
        }
    )

    pg = next((r for r in corrected_results if r.metric == "peak_gain"), None)
    pg_status = pg.status if pg else None

    if not violations:
        if extraction_phase < max_phase and has_s11 and extraction_phase < 2 and any(
            r.metric in mandatory and r.status == MetricStatus.INSUFFICIENT_EVIDENCE for r in corrected_results
        ):
            return VerifierDecision(
                action=VerifierAction.RETRY_EVIDENCE,
                approved=False,
                review=corrected,
                violations=["Mandatory metrics missing — invoke S11 tools"],
            )
        if _needs_notes_pass(has_notes, extraction_phase, evidence, pg_status):
            return VerifierDecision(
                action=VerifierAction.RETRY_EVIDENCE,
                approved=False,
                review=corrected,
                violations=["Gain requires notes cross-check before final verdict"],
            )
        return VerifierDecision(action=VerifierAction.APPROVE, approved=True, review=corrected, violations=[])

    if missing_citable and extraction_phase < max_phase:
        return VerifierDecision(
            action=VerifierAction.RETRY_EVIDENCE,
            approved=False,
            review=corrected,
            violations=violations,
        )

    if proposed.overall_verdict == OverallVerdict.PASS and violations:
        abstain = corrected.model_copy(
            update={
                "overall_verdict": OverallVerdict.INSUFFICIENT_EVIDENCE,
                "rationale": "Verifier abstains: cannot prove PASS with current evidence.",
            }
        )
        return VerifierDecision(action=VerifierAction.ABSTAIN, approved=False, review=abstain, violations=violations)

    return VerifierDecision(action=VerifierAction.APPROVE, approved=True, review=corrected, violations=violations)
