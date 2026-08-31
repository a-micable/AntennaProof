"""Design review judgment from evidence + criteria only (no bundle, no gold labeler)."""

from __future__ import annotations

from src.schemas import (
    AcceptanceCriteria,
    CriterionSpec,
    EvidenceItem,
    MetricResult,
    MetricStatus,
    OverallVerdict,
    ProposedReview,
)
from src.tools.unit_normalizer import frequencies_conflict, parse_frequency


def _metric_key(name: str) -> str:
    if name in ("min_s11", "minimum_s11"):
        return "minimum_s11"
    return name


def _required_label(c: CriterionSpec) -> str:
    if c.operator == "in_range":
        return f"{c.min_value}–{c.max_value} {c.unit}"
    if c.operator == "gte":
        return f"≥{c.value} {c.unit}"
    if c.operator == "lte":
        return f"≤{c.value} {c.unit}"
    return c.description


def _canonical_freq(items: list[EvidenceItem]) -> tuple[float | None, list[str]]:
    vals: list[tuple[str, float]] = []
    ids: list[str] = []
    for e in items:
        if e.metric != "resonant_frequency" or e.value is None:
            continue
        if e.unit.lower() in ("ghz",):
            v = float(e.value)
        elif e.unit.lower() in ("mhz",):
            v = parse_frequency(float(e.value), "MHz").canonical_value
        else:
            v = float(e.value)
        vals.append((e.evidence_id, v))
        ids.append(e.evidence_id)
    if not vals:
        return None, ids
    if len(vals) > 1 and any(frequencies_conflict(vals[0][1], v) for _, v in vals[1:]):
        return None, ids  # conflict signal
    return vals[0][1], ids


def _best_evidence(items: list[EvidenceItem], prefer: str = "measurements.json") -> EvidenceItem | None:
    if not items:
        return None
    for e in items:
        if e.source == prefer:
            return e
    return items[0]


def _judge_metric(
    criterion: CriterionSpec,
    evidence: list[EvidenceItem],
    mandatory: bool,
    fail_on_multi: bool,
) -> MetricResult:
    metric = criterion.metric
    required = _required_label(criterion)
    related = [e for e in evidence if e.metric == metric or (metric == "peak_gain" and e.metric == "peak_gain_claimed")]

    if metric == "resonant_frequency":
        resonance = [e for e in evidence if e.metric == "resonance_count"]
        freq, eids = _canonical_freq([e for e in evidence if e.metric == "resonant_frequency"])
        if resonance and resonance[0].value and float(resonance[0].value) > 1 and fail_on_multi:
            return MetricResult(
                metric=metric,
                required=required,
                measured=str(freq) if freq else None,
                status=MetricStatus.INSUFFICIENT_EVIDENCE,
                evidence_id=resonance[0].evidence_id,
                reason=f"Multiple resonances detected ({int(float(resonance[0].value))})",
            )
        if freq is None and eids:
            return MetricResult(
                metric=metric,
                required=required,
                measured=None,
                status=MetricStatus.INSUFFICIENT_EVIDENCE,
                evidence_id=eids[0],
                reason="Conflicting frequency values across sources.",
            )
        if freq is None:
            return MetricResult(metric=metric, required=required, measured=None, status=MetricStatus.INSUFFICIENT_EVIDENCE, reason="No frequency evidence.")
        be = _best_evidence([e for e in evidence if e.metric == "resonant_frequency"])
        if freq < (criterion.min_value or 0) or freq > (criterion.max_value or 99):
            return MetricResult(metric=metric, required=required, measured=f"{freq} GHz", status=MetricStatus.FAIL, evidence_id=be.evidence_id if be else None, reason="Outside required band.")
        return MetricResult(metric=metric, required=required, measured=f"{freq} GHz", status=MetricStatus.PASS, evidence_id=be.evidence_id if be else None)

    if metric == "peak_gain":
        json_items = [e for e in evidence if e.metric == "peak_gain"]
        note_items = [e for e in evidence if e.metric == "peak_gain_claimed"]
        dir_items = [e for e in evidence if e.metric == "peak_directivity"]
        j = json_items[0] if json_items else None
        n = note_items[0] if note_items else None
        if j and n and abs(float(j.value) - float(n.value)) > 0.25:
            return MetricResult(
                metric=metric,
                required=required,
                measured=str(j.value),
                status=MetricStatus.INSUFFICIENT_EVIDENCE,
                evidence_id=j.evidence_id,
                reason=f"Contradiction: notes claim {n.value} dBi vs measurements.json={j.value} dBi",
            )
        if not j and dir_items:
            return MetricResult(
                metric=metric,
                required=required,
                measured=str(dir_items[0].value),
                status=MetricStatus.INSUFFICIENT_EVIDENCE,
                evidence_id=dir_items[0].evidence_id,
                reason="Only directivity reported; gain required.",
            )
        be = j or n
        if not be:
            return MetricResult(metric=metric, required=required, measured=None, status=MetricStatus.INSUFFICIENT_EVIDENCE, reason="No gain evidence.")
        val = float(be.value)
        if val < (criterion.value or 0):
            return MetricResult(metric=metric, required=required, measured=f"{val} dBi", status=MetricStatus.FAIL, evidence_id=be.evidence_id, reason="Gain below minimum.")
        return MetricResult(metric=metric, required=required, measured=f"{val} dBi", status=MetricStatus.PASS, evidence_id=be.evidence_id)

    if metric == "bandwidth":
        resonance = [e for e in evidence if e.metric == "resonance_count"]
        bw_items = [e for e in evidence if e.metric == "bandwidth"]
        if resonance and resonance[0].value and float(resonance[0].value) > 1:
            be = bw_items[0] if bw_items else resonance[0]
            if bw_items:
                val = float(bw_items[0].value)
                st = MetricStatus.FAIL if val < (criterion.value or 0) else MetricStatus.INSUFFICIENT_EVIDENCE
                return MetricResult(metric=metric, required=required, measured=f"{val} MHz", status=st, evidence_id=be.evidence_id, reason=f"Multiple resonances detected ({int(float(resonance[0].value))})")
        be = _best_evidence(bw_items)
        if not be:
            return MetricResult(metric=metric, required=required, measured=None, status=MetricStatus.INSUFFICIENT_EVIDENCE, reason="No bandwidth evidence.")
        val = float(be.value)
        if val < (criterion.value or 0):
            return MetricResult(metric=metric, required=required, measured=f"{val} MHz", status=MetricStatus.FAIL, evidence_id=be.evidence_id, reason=f"{val} MHz below minimum {criterion.value} MHz")
        return MetricResult(metric=metric, required=required, measured=f"{val} MHz", status=MetricStatus.PASS, evidence_id=be.evidence_id)

    if metric == "minimum_s11":
        items = [e for e in evidence if e.metric == "minimum_s11"]
        be = _best_evidence(items)
        if not be:
            return MetricResult(metric=metric, required=required, measured=None, status=MetricStatus.INSUFFICIENT_EVIDENCE, reason="No S11 evidence.")
        val = float(be.value)
        if val > (criterion.value or -10):
            return MetricResult(metric=metric, required=required, measured=f"{val} dB", status=MetricStatus.FAIL, evidence_id=be.evidence_id, reason="S11 above threshold.")
        return MetricResult(metric=metric, required=required, measured=f"{val} dB", status=MetricStatus.PASS, evidence_id=be.evidence_id)

    if metric == "efficiency":
        items = [e for e in evidence if e.metric == "efficiency"]
        be = items[0] if items else None
        if not be:
            st = MetricStatus.INSUFFICIENT_EVIDENCE
            reason = "No evidence for efficiency." if mandatory else "Optional metric not provided."
            return MetricResult(metric=metric, required=required, measured=None, status=st, reason=reason)
        val = float(be.value)
        if val < (criterion.value or 0):
            return MetricResult(metric=metric, required=required, measured=f"{val}%", status=MetricStatus.FAIL, evidence_id=be.evidence_id, reason="Efficiency below minimum.")
        return MetricResult(metric=metric, required=required, measured=f"{val}%", status=MetricStatus.PASS, evidence_id=be.evidence_id)

    return MetricResult(metric=metric, required=required, measured=None, status=MetricStatus.INSUFFICIENT_EVIDENCE, reason="Unknown metric.")


def review_from_evidence(
    criteria: AcceptanceCriteria,
    evidence: list[EvidenceItem],
    *,
    fail_on_multi_resonance: bool = False,
) -> ProposedReview:
    """Judge ONLY from evidence items — independent of gold labeler."""
    mandatory_keys = {_metric_key(m) for m in criteria.mandatory_metrics}
    results: list[MetricResult] = []

    for c in criteria.criteria:
        is_mandatory = _metric_key(c.metric) in mandatory_keys
        results.append(
            _judge_metric(c, evidence, is_mandatory, fail_on_multi_resonance)
        )

    mandatory_results = [r for r in results if _metric_key(r.metric) in mandatory_keys]
    if any(r.status == MetricStatus.FAIL for r in mandatory_results):
        overall = OverallVerdict.FAIL
    elif any(r.status == MetricStatus.INSUFFICIENT_EVIDENCE for r in mandatory_results):
        overall = OverallVerdict.INSUFFICIENT_EVIDENCE
    else:
        overall = OverallVerdict.PASS

    covered = sum(1 for r in mandatory_results if r.measured is not None)
    coverage = (covered / len(mandatory_results) * 100) if mandatory_results else 0.0

    return ProposedReview(
        overall_verdict=overall,
        metric_results=results,
        insufficient_evidence=[f"{r.metric}: {r.reason}" for r in results if r.status == MetricStatus.INSUFFICIENT_EVIDENCE],
        confidence="high" if coverage >= 80 else "medium",
        evidence_coverage_percent=round(coverage, 1),
        rationale="Review derived from cited evidence only.",
    )
