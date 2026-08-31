"""Shared deterministic evaluation rules for review and ground truth."""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.schemas import (
    AcceptanceCriteria,
    EvidenceItem,
    GroundTruth,
    GroundTruthMetric,
    MetricResult,
    MetricStatus,
    OverallVerdict,
    ProposedReview,
)
from src.tools.case_loader import CaseBundle
from src.tools.unit_normalizer import frequencies_conflict, parse_frequency


def _metric_key(name: str) -> str:
    if name in ("min_s11", "minimum_s11"):
        return "minimum_s11"
    return name


def _req_str(metric: str, criteria: dict) -> str:
    c = criteria.get(metric, criteria.get("min_s11" if metric == "minimum_s11" else metric, {}))
    if metric == "resonant_frequency":
        return f"{c.get('min_ghz', '?')}–{c.get('max_ghz', '?')} GHz"
    if metric == "bandwidth":
        return f"≥{c.get('min_mhz', '?')} MHz"
    if metric == "peak_gain":
        return f"≥{c.get('min_dbi', '?')} dBi"
    if metric == "minimum_s11":
        c = criteria.get("minimum_s11", criteria.get("min_s11", {}))
        return f"≤{c.get('max_db', '?')} dB"
    if metric == "efficiency":
        return f"≥{c.get('min_percent', '?')}%"
    return "?"


def _note_gain(notes: str) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)\s*dBi", notes, re.I)
    return float(m.group(1)) if m else None


@dataclass
class MetricEval:
    metric: str
    status: MetricStatus
    measured: float | None
    required: str
    reason: str


def _eval_resonant_frequency(bundle: CaseBundle, criteria: dict) -> MetricEval:
    metric = "resonant_frequency"
    required = _req_str(metric, criteria)
    c = criteria.get(metric, {})
    meas = bundle.measurements

    json_sources: list[float] = []
    if meas.get("resonant_frequency_ghz") is not None:
        json_sources.append(float(meas["resonant_frequency_ghz"]))
    if meas.get("resonant_frequency_mhz") is not None:
        json_sources.append(parse_frequency(meas["resonant_frequency_mhz"], "MHz").canonical_value)

    if len(json_sources) > 1 and any(frequencies_conflict(json_sources[0], v) for v in json_sources[1:]):
        return MetricEval(
            metric,
            MetricStatus.INSUFFICIENT_EVIDENCE,
            json_sources[0],
            required,
            "Conflicting frequency values across sources.",
        )

    val = json_sources[0] if json_sources else None
    if val is None and bundle.s11_analysis:
        val = bundle.s11_analysis.resonant_frequency_ghz

    if bundle.s11_analysis and bundle.s11_analysis.resonance_count > 1:
        s11_driven = not json_sources
        if bundle.requirements.get("fail_on_multi_resonance") or s11_driven:
            return MetricEval(
                metric,
                MetricStatus.INSUFFICIENT_EVIDENCE,
                val,
                required,
                f"Multiple resonances detected ({bundle.s11_analysis.resonance_count})",
            )

    if val is None:
        return MetricEval(metric, MetricStatus.INSUFFICIENT_EVIDENCE, None, required, "No frequency evidence.")

    if val < c.get("min_ghz", float("-inf")) or val > c.get("max_ghz", float("inf")):
        return MetricEval(metric, MetricStatus.FAIL, val, required, "Outside required band.")
    return MetricEval(metric, MetricStatus.PASS, val, required, "")


def _eval_bandwidth(bundle: CaseBundle, criteria: dict) -> MetricEval:
    metric = "bandwidth"
    required = _req_str(metric, criteria)
    c = criteria.get(metric, {})
    bw = bundle.measurements.get("bandwidth_mhz")
    if bw is None and bundle.s11_analysis:
        bw = bundle.s11_analysis.bandwidth_mhz
    if bundle.s11_analysis and bundle.s11_analysis.resonance_count > 1:
        s11_driven = bundle.measurements.get("bandwidth_mhz") is None
        if bundle.requirements.get("fail_on_multi_resonance") or s11_driven:
            bw = bundle.s11_analysis.bandwidth_mhz
            return MetricEval(
                metric,
                MetricStatus.FAIL if bw is not None else MetricStatus.INSUFFICIENT_EVIDENCE,
                bw,
                required,
                f"Multiple resonances detected ({bundle.s11_analysis.resonance_count})",
            )
    if bw is None:
        return MetricEval(metric, MetricStatus.INSUFFICIENT_EVIDENCE, None, required, "No bandwidth evidence.")
    if float(bw) < float(c.get("min_mhz", 0)):
        return MetricEval(metric, MetricStatus.FAIL, float(bw), required, f"{bw} MHz below minimum {c.get('min_mhz')} MHz")
    return MetricEval(metric, MetricStatus.PASS, float(bw), required, "")


def _eval_peak_gain(bundle: CaseBundle, criteria: dict) -> MetricEval:
    metric = "peak_gain"
    required = _req_str(metric, criteria)
    c = criteria.get(metric, {})
    json_gain = bundle.measurements.get("peak_gain_dbi")
    directivity = bundle.measurements.get("peak_directivity_dbi")
    note_gain = _note_gain(bundle.notes)

    if json_gain is not None and note_gain is not None and abs(json_gain - note_gain) > 0.25:
        return MetricEval(
            metric,
            MetricStatus.INSUFFICIENT_EVIDENCE,
            json_gain,
            required,
            f"Contradiction: notes claim {note_gain} dBi vs measurements.json={json_gain} dBi",
        )

    if json_gain is None and directivity is not None:
        return MetricEval(
            metric,
            MetricStatus.INSUFFICIENT_EVIDENCE,
            directivity,
            required,
            "Only directivity reported; gain required.",
        )

    val = json_gain if json_gain is not None else note_gain
    if val is None:
        return MetricEval(metric, MetricStatus.INSUFFICIENT_EVIDENCE, None, required, "No gain evidence.")
    if float(val) < float(c.get("min_dbi", 0)):
        return MetricEval(metric, MetricStatus.FAIL, float(val), required, "Gain below minimum.")
    return MetricEval(metric, MetricStatus.PASS, float(val), required, "")


def _eval_minimum_s11(bundle: CaseBundle, criteria: dict) -> MetricEval:
    metric = "minimum_s11"
    required = _req_str(metric, criteria)
    c = criteria.get("minimum_s11", criteria.get("min_s11", {}))
    val = bundle.measurements.get("minimum_s11_db", bundle.measurements.get("min_s11_db"))
    if val is None and bundle.s11_analysis:
        val = bundle.s11_analysis.minimum_s11_db
    if val is None:
        return MetricEval(metric, MetricStatus.INSUFFICIENT_EVIDENCE, None, required, "No S11 evidence.")
    if float(val) > float(c.get("max_db", -10)):
        return MetricEval(metric, MetricStatus.FAIL, float(val), required, "S11 above threshold.")
    return MetricEval(metric, MetricStatus.PASS, float(val), required, "")


def _eval_efficiency(bundle: CaseBundle, criteria: dict, mandatory: bool) -> MetricEval:
    metric = "efficiency"
    required = _req_str(metric, criteria)
    c = criteria.get(metric, {})
    val = bundle.measurements.get("efficiency_percent")
    if val is None:
        if mandatory:
            return MetricEval(metric, MetricStatus.INSUFFICIENT_EVIDENCE, None, required, f"No evidence for efficiency in {bundle.case_id.lower()}")
        return MetricEval(metric, MetricStatus.INSUFFICIENT_EVIDENCE, None, required, "Optional metric not provided.")
    if float(val) < float(c.get("min_percent", 0)):
        return MetricEval(metric, MetricStatus.FAIL, float(val), required, "Efficiency below minimum.")
    return MetricEval(metric, MetricStatus.PASS, float(val), required, "")


def evaluate_metrics(bundle: CaseBundle, criteria: AcceptanceCriteria) -> list[MetricEval]:
    raw = bundle.requirements.get("criteria", {})
    metrics_to_eval = list(criteria.mandatory_metrics) + list(criteria.optional_metrics)
    seen: set[str] = set()
    ordered: list[str] = []
    for m in metrics_to_eval:
        key = _metric_key(m)
        if key not in seen:
            seen.add(key)
            ordered.append(key)

    results: list[MetricEval] = []
    for metric in ordered:
        if metric == "resonant_frequency":
            results.append(_eval_resonant_frequency(bundle, raw))
        elif metric == "bandwidth":
            results.append(_eval_bandwidth(bundle, raw))
        elif metric == "peak_gain":
            results.append(_eval_peak_gain(bundle, raw))
        elif metric == "minimum_s11":
            results.append(_eval_minimum_s11(bundle, raw))
        elif metric == "efficiency":
            mandatory = metric in criteria.mandatory_metrics or "efficiency" in criteria.mandatory_metrics
            results.append(_eval_efficiency(bundle, raw, mandatory))
    return results


def overall_verdict(metric_evals: list[MetricEval], mandatory: list[str]) -> OverallVerdict:
    mandatory_keys = {_metric_key(m) for m in mandatory}
    relevant = [m for m in metric_evals if m.metric in mandatory_keys]
    if any(m.status == MetricStatus.FAIL for m in relevant):
        return OverallVerdict.FAIL
    if any(m.status == MetricStatus.INSUFFICIENT_EVIDENCE for m in relevant):
        return OverallVerdict.INSUFFICIENT_EVIDENCE
    return OverallVerdict.PASS


def overall_verdict_from_results(metric_results: list[MetricResult], mandatory: list[str]) -> OverallVerdict:
    mandatory_keys = {_metric_key(m) for m in mandatory}
    relevant = [m for m in metric_results if m.metric in mandatory_keys]
    if any(m.status == MetricStatus.FAIL for m in relevant):
        return OverallVerdict.FAIL
    if any(m.status == MetricStatus.INSUFFICIENT_EVIDENCE for m in relevant):
        return OverallVerdict.INSUFFICIENT_EVIDENCE
    return OverallVerdict.PASS


def evaluate_bundle(bundle: CaseBundle, criteria: AcceptanceCriteria) -> ProposedReview:
    evals = evaluate_metrics(bundle, criteria)
    mandatory = [_metric_key(m) for m in criteria.mandatory_metrics]
    overall = overall_verdict(evals, mandatory)

    insufficient = [f"{e.metric}: {e.reason}" for e in evals if e.status == MetricStatus.INSUFFICIENT_EVIDENCE]
    metric_results = [
        MetricResult(
            metric=e.metric,
            required=e.required,
            measured=str(e.measured) if e.measured is not None else None,
            status=e.status,
            reason=e.reason,
        )
        for e in evals
    ]

    covered = sum(1 for m in metric_results if m.metric in mandatory and m.measured is not None)
    coverage = (covered / len(mandatory) * 100) if mandatory else 0.0

    notes = "All mandatory metrics pass with sufficient evidence"
    if overall == OverallVerdict.FAIL:
        notes = "One or more mandatory metrics failed thresholds"
    elif overall == OverallVerdict.INSUFFICIENT_EVIDENCE:
        notes = "One or more mandatory metrics lack sufficient evidence"

    return ProposedReview(
        overall_verdict=overall,
        metric_results=metric_results,
        insufficient_evidence=insufficient,
        confidence="high" if coverage >= 80 else "medium",
        evidence_coverage_percent=round(coverage, 1),
        rationale=notes,
    )


def evaluate_to_ground_truth(bundle: CaseBundle, criteria: AcceptanceCriteria) -> GroundTruth:
    evals = evaluate_metrics(bundle, criteria)
    mandatory = [_metric_key(m) for m in criteria.mandatory_metrics]
    overall = overall_verdict(evals, mandatory)
    notes = "All mandatory metrics pass with sufficient evidence"
    if overall == OverallVerdict.FAIL:
        notes = "One or more mandatory metrics failed thresholds"
    elif overall == OverallVerdict.INSUFFICIENT_EVIDENCE:
        notes = "One or more mandatory metrics lack sufficient evidence"

    return GroundTruth(
        case_id=bundle.case_id,
        overall_verdict=overall,
        metrics=[
            GroundTruthMetric(
                metric=e.metric,
                status=e.status,
                required=e.required,
                measured=e.measured,
                reason=e.reason,
            )
            for e in evals
        ],
        notes=notes,
    )


def attach_evidence_ids(review: ProposedReview, evidence: list[EvidenceItem]) -> ProposedReview:
    by_metric = {e.metric: e.evidence_id for e in evidence}
    alias = {
        "peak_gain_claimed": "peak_gain",
    }
    updated: list[MetricResult] = []
    for mr in review.metric_results:
        eid = by_metric.get(mr.metric)
        if not eid:
            for k, v in alias.items():
                if v == mr.metric and k in by_metric:
                    eid = by_metric[k]
        updated.append(mr.model_copy(update={"evidence_id": eid}))
    return review.model_copy(update={"metric_results": updated})
