"""Baseline — single-pass monolithic review without verification."""

from __future__ import annotations

import re

from src.schemas import MetricResult, MetricStatus, OverallVerdict, ProposedReview
from src.tools.case_loader import CaseBundle


def run_baseline(bundle: CaseBundle) -> ProposedReview:
    """
    Fair baseline: one function reads measurements and decides PASS/FAIL.
    Weaknesses (intentional realistic gaps):
    - Ignores notes/measurement contradictions
    - Treats peak_directivity as peak_gain
    - Ignores multi-resonance S11 flags
    - Ignores unit conflicts (uses first frequency field only)
    - Missing mandatory metrics may still yield PASS
    - Adversarial notes can be trusted if measurements look mostly fine
    """
    meas = bundle.measurements
    req = bundle.requirements
    criteria = req.get("criteria", {})
    mandatory = req.get("mandatory_metrics", [])
    metric_results: list[MetricResult] = []

    def add(metric: str, required: str, measured: str | None, status: MetricStatus, reason: str = ""):
        metric_results.append(
            MetricResult(metric=metric, required=required, measured=measured, status=status, reason=reason)
        )

    # Resonant frequency — first field only, no conflict check
    rf = meas.get("resonant_frequency_ghz")
    if rf is None and meas.get("resonant_frequency_mhz") is not None:
        rf = float(meas["resonant_frequency_mhz"]) / 1000.0
    c = criteria.get("resonant_frequency", {})
    req_rf = f"{c.get('min_ghz', '?')}–{c.get('max_ghz', '?')} GHz"
    if rf is None:
        add("resonant_frequency", req_rf, None, MetricStatus.INSUFFICIENT_EVIDENCE, "Missing")
    elif rf < c.get("min_ghz", 0) or rf > c.get("max_ghz", 99):
        add("resonant_frequency", req_rf, f"{rf} GHz", MetricStatus.FAIL, "Out of band")
    else:
        add("resonant_frequency", req_rf, f"{rf} GHz", MetricStatus.PASS)

    # Bandwidth
    bw = meas.get("bandwidth_mhz")
    c = criteria.get("bandwidth", {})
    req_bw = f"≥{c.get('min_mhz', '?')} MHz"
    if bw is None:
        add("bandwidth", req_bw, None, MetricStatus.INSUFFICIENT_EVIDENCE, "Missing")
    elif float(bw) < float(c.get("min_mhz", 0)):
        add("bandwidth", req_bw, f"{bw} MHz", MetricStatus.FAIL, "Too narrow")
    else:
        add("bandwidth", req_bw, f"{bw} MHz", MetricStatus.PASS)

    # Gain — accepts directivity (baseline weakness)
    gain = meas.get("peak_gain_dbi", meas.get("peak_directivity_dbi"))
    if gain is None and bundle.notes:
        m = re.search(r"(\d+(?:\.\d+)?)\s*dBi", bundle.notes, re.I)
        if m:
            gain = float(m.group(1))
    c = criteria.get("peak_gain", {})
    req_g = f"≥{c.get('min_dbi', '?')} dBi"
    if gain is None:
        add("peak_gain", req_g, None, MetricStatus.INSUFFICIENT_EVIDENCE, "Missing")
    elif float(gain) < float(c.get("min_dbi", 0)):
        add("peak_gain", req_g, f"{gain} dBi", MetricStatus.FAIL, "Too low")
    else:
        add("peak_gain", req_g, f"{gain} dBi", MetricStatus.PASS)

    # S11
    s11 = meas.get("minimum_s11_db", meas.get("min_s11_db"))
    c = criteria.get("minimum_s11", criteria.get("min_s11", {}))
    req_s = f"≤{c.get('max_db', '?')} dB"
    if s11 is None:
        add("minimum_s11", req_s, None, MetricStatus.INSUFFICIENT_EVIDENCE, "Missing")
    elif float(s11) > float(c.get("max_db", -10)):
        add("minimum_s11", req_s, f"{s11} dB", MetricStatus.FAIL, "Above threshold")
    else:
        add("minimum_s11", req_s, f"{s11} dB", MetricStatus.PASS)

    # Efficiency — baseline often skips if not in JSON (weakness)
    if "efficiency" in mandatory:
        eff = meas.get("efficiency_percent")
        c = criteria.get("efficiency", {})
        req_e = f"≥{c.get('min_percent', '?')}%"
        if eff is None:
            add("efficiency", req_e, None, MetricStatus.INSUFFICIENT_EVIDENCE, "Missing")
        elif float(eff) < float(c.get("min_percent", 0)):
            add("efficiency", req_e, f"{eff}%", MetricStatus.FAIL, "Too low")
        else:
            add("efficiency", req_e, f"{eff}%", MetricStatus.PASS)

    # Baseline overall: optimistic — PASS unless explicit FAIL seen
    has_fail = any(m.status == MetricStatus.FAIL for m in metric_results)
    has_ie = any(m.status == MetricStatus.INSUFFICIENT_EVIDENCE for m in metric_results)

    if has_fail:
        overall = OverallVerdict.FAIL
    elif has_ie and "efficiency" in mandatory:
        overall = OverallVerdict.INSUFFICIENT_EVIDENCE
    elif has_ie:
        # Baseline weakness: ignore IE on optional/missing unless all empty
        if len(meas) == 0:
            overall = OverallVerdict.INSUFFICIENT_EVIDENCE
        else:
            overall = OverallVerdict.PASS
    else:
        overall = OverallVerdict.PASS

    # Adversarial weakness: trust notes saying pass (if no hard fail)
    if bundle.notes and "mark pass" in bundle.notes.lower() and not has_fail:
        overall = OverallVerdict.PASS
        for i, m in enumerate(metric_results):
            if m.status == MetricStatus.FAIL:
                continue
            if m.status == MetricStatus.INSUFFICIENT_EVIDENCE:
                metric_results[i] = m.model_copy(update={"status": MetricStatus.PASS, "reason": "Trusted note"})

    covered = sum(1 for m in metric_results if m.measured)
    coverage = (covered / len(metric_results) * 100) if metric_results else 0

    return ProposedReview(
        overall_verdict=overall,
        metric_results=metric_results,
        insufficient_evidence=[f"{m.metric}: {m.reason}" for m in metric_results if m.status == MetricStatus.INSUFFICIENT_EVIDENCE],
        confidence="medium",
        evidence_coverage_percent=round(coverage, 1),
        rationale="Baseline single-pass review (no verifier)",
    )
