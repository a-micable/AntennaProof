"""Programmatic ground-truth computation for evaluation cases."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.schemas import GroundTruth, GroundTruthMetric, MetricStatus, OverallVerdict
from src.tools.case_loader import load_case, list_cases
from src.tools.s11_analyzer import analyze_s11_csv
from src.tools.unit_normalizer import (
    frequencies_conflict,
    parse_bandwidth,
    parse_efficiency_percent,
    parse_frequency,
    parse_gain_db,
    parse_s11_db,
)


def _metric_ie(name: str, required: str, rationale: str) -> GroundTruthMetric:
    return GroundTruthMetric(
        metric=name,
        status=MetricStatus.INSUFFICIENT_EVIDENCE,
        required=required,
        measured=None,
        rationale=rationale,
    )


def _metric_pass(name: str, required: str, measured: str) -> GroundTruthMetric:
    return GroundTruthMetric(
        metric=name,
        status=MetricStatus.PASS,
        required=required,
        measured=measured,
        rationale="Meets threshold with consistent evidence.",
    )


def _metric_fail(name: str, required: str, measured: str, rationale: str) -> GroundTruthMetric:
    return GroundTruthMetric(
        metric=name,
        status=MetricStatus.FAIL,
        required=required,
        measured=measured,
        rationale=rationale,
    )


def _extract_note_gain(notes: str) -> float | None:
    m = re.search(r"peak\s+gain\s*(?:is|:)?\s*([0-9.]+)\s*dBi", notes, re.I)
    if m:
        return parse_gain_db(m.group(1))
    m = re.search(r"gain\s*(?:is|:)?\s*([0-9.]+)\s*dBi", notes, re.I)
    return parse_gain_db(m.group(1)) if m else None


def _extract_note_directivity(notes: str) -> float | None:
    m = re.search(r"directivity\s*(?:is|:)?\s*([0-9.]+)\s*dBi", notes, re.I)
    return parse_gain_db(m.group(1)) if m else None


def _overall(metrics: list[GroundTruthMetric]) -> OverallVerdict:
    mandatory = [m for m in metrics if m.status != MetricStatus.PASS or True]
    if any(m.status == MetricStatus.INSUFFICIENT_EVIDENCE for m in metrics):
        return OverallVerdict.INSUFFICIENT_EVIDENCE
    if any(m.status == MetricStatus.FAIL for m in metrics):
        return OverallVerdict.FAIL
    return OverallVerdict.PASS


def compute_ground_truth(case_dir: Path) -> GroundTruth:
    bundle = load_case(case_dir)
    req = bundle.requirements
    meas = bundle.measurements
    criteria = req.get("criteria", {})
    mandatory = set(req.get("mandatory_metrics", []))
    metrics: list[GroundTruthMetric] = []

    # Adversarial injection should not change deterministic truth from measurements
    if bundle.notes and "ignore requirements" in bundle.notes.lower():
        pass  # handled by still using measurements; verdict from data only

    s11 = None
    if bundle.s11_path:
        s11 = analyze_s11_csv(bundle.s11_path)

    # --- resonant frequency ---
    if "resonant_frequency" in mandatory or "resonant_frequency" in criteria:
        c = criteria.get("resonant_frequency", {})
        req_str = f"{c.get('min_ghz', '?')}–{c.get('max_ghz', '?')} GHz"
        freq_meas = None
        freq_from_meas = meas.get("resonant_frequency_ghz")
        freq_from_meas_mhz = meas.get("resonant_frequency_mhz")
        freq_from_meas_alt = meas.get("resonant_frequency")

        sources: list[tuple[str, float]] = []
        if freq_from_meas is not None:
            sources.append(("measurements.json", float(freq_from_meas)))
        if freq_from_meas_mhz is not None:
            sources.append(("measurements.json", parse_frequency(freq_from_meas_mhz, "MHz").canonical_value))
        if freq_from_meas_alt is not None:
            unit = meas.get("resonant_frequency_unit", "GHz")
            sources.append(("measurements.json", parse_frequency(freq_from_meas_alt, unit).canonical_value))
        if s11 and s11.resonant_frequency_ghz is not None:
            sources.append(("s11.csv", s11.resonant_frequency_ghz))

        if not sources:
            metrics.append(_metric_ie("resonant_frequency", req_str, "No frequency evidence."))
        elif len(sources) > 1 and any(
            frequencies_conflict(sources[0][1], v) for _, v in sources[1:]
        ):
            metrics.append(
                _metric_ie(
                    "resonant_frequency",
                    req_str,
                    "Conflicting frequency values across sources.",
                )
            )
        else:
            val = sources[0][1]
            measured = f"{val:.4f} GHz"
            if val < c.get("min_ghz", float("-inf")) or val > c.get("max_ghz", float("inf")):
                metrics.append(_metric_fail("resonant_frequency", req_str, measured, "Outside required band."))
            else:
                metrics.append(_metric_pass("resonant_frequency", req_str, measured))

    # --- bandwidth ---
    if "bandwidth" in mandatory or "bandwidth" in criteria:
        c = criteria.get("bandwidth", {})
        req_str = f"≥{c.get('min_mhz', '?')} MHz"
        bw = meas.get("bandwidth_mhz")
        if bw is None and s11:
            bw = s11.bandwidth_mhz
        if bw is None:
            metrics.append(_metric_ie("bandwidth", req_str, "No bandwidth evidence."))
        else:
            measured = f"{float(bw):.2f} MHz"
            if float(bw) < float(c.get("min_mhz", 0)):
                metrics.append(_metric_fail("bandwidth", req_str, measured, "Below minimum bandwidth."))
            else:
                metrics.append(_metric_pass("bandwidth", req_str, measured))

    # --- peak gain ---
    if "peak_gain" in mandatory or "peak_gain" in criteria:
        c = criteria.get("peak_gain", {})
        req_str = f"≥{c.get('min_dbi', '?')} dBi"
        gain_json = meas.get("peak_gain_dbi")
        note_gain = _extract_note_gain(bundle.notes)
        directivity = _extract_note_directivity(bundle.notes)

        if gain_json is None and note_gain is None:
            metrics.append(_metric_ie("peak_gain", req_str, "No gain evidence."))
        elif gain_json is not None and note_gain is not None and abs(gain_json - note_gain) > 0.05:
            metrics.append(_metric_ie("peak_gain", req_str, "Conflicting gain in notes vs measurements."))
        elif directivity is not None and gain_json is None and note_gain is None:
            measured = f"{directivity:.2f} dBi (directivity)"
            metrics.append(
                _metric_fail(
                    "peak_gain",
                    req_str,
                    measured,
                    "Directivity reported where gain is required.",
                )
            )
        else:
            val = gain_json if gain_json is not None else note_gain
            if val is None and meas.get("peak_directivity_dbi") is not None:
                val = meas["peak_directivity_dbi"]
                measured = f"{float(val):.2f} dBi (directivity)"
                metrics.append(
                    _metric_fail("peak_gain", req_str, measured, "Directivity used instead of gain.")
                )
            else:
                measured = f"{float(val):.2f} dBi"
                if float(val) < float(c.get("min_dbi", 0)):
                    metrics.append(_metric_fail("peak_gain", req_str, measured, "Gain below minimum."))
                else:
                    metrics.append(_metric_pass("peak_gain", req_str, measured))

    # --- min s11 ---
    if "min_s11" in mandatory or "min_s11" in criteria:
        c = criteria.get("min_s11", {})
        req_str = f"≤{c.get('max_db', '?')} dB"
        s11_val = meas.get("min_s11_db")
        if s11_val is None and s11:
            s11_val = s11.min_s11_db
        if s11_val is None:
            metrics.append(_metric_ie("min_s11", req_str, "No S11 evidence."))
        else:
            measured = f"{float(s11_val):.2f} dB"
            if float(s11_val) > float(c.get("max_db", -10)):
                metrics.append(_metric_fail("min_s11", req_str, measured, "S11 above threshold."))
            else:
                metrics.append(_metric_pass("min_s11", req_str, measured))

    # --- efficiency (optional unless mandatory) ---
    eff_required = "efficiency" in mandatory
    if eff_required or "efficiency" in criteria:
        c = criteria.get("efficiency", {})
        req_str = f"≥{c.get('min_percent', '?')}%"
        eff = meas.get("efficiency_percent")
        if eff is None:
            if eff_required:
                metrics.append(_metric_ie("efficiency", req_str, "Mandatory efficiency missing."))
        else:
            measured = f"{float(eff):.2f}%"
            if float(eff) < float(c.get("min_percent", 0)):
                metrics.append(_metric_fail("efficiency", req_str, measured, "Efficiency below minimum."))
            else:
                metrics.append(_metric_pass("efficiency", req_str, measured))

    # --- multi-resonance flag ---
    if s11 and s11.resonance_count > 1 and req.get("fail_on_multi_resonance"):
        # Override: treat as fail if not already IE
        for i, m in enumerate(metrics):
            if m.metric == "resonant_frequency" and m.status == MetricStatus.PASS:
                metrics[i] = _metric_fail(
                    "resonant_frequency",
                    m.required,
                    m.measured or "",
                    "Multiple resonances detected in S11.",
                )

    # Filter to mandatory-only for overall unless efficiency optional passed
    mandatory_names = set(mandatory)
    verdict_metrics = [m for m in metrics if m.metric in mandatory_names or m.metric in criteria]

    verdict = _overall(verdict_metrics)
    return GroundTruth(
        case_id=bundle.case_id,
        overall_verdict=verdict,
        metrics=metrics,
        notes=f"Computed from {case_dir.name}",
    )


def write_all(data_root: Path) -> None:
    for case_dir in list_cases(data_root):
        gt = compute_ground_truth(case_dir)
        out = case_dir / "ground_truth.json"
        out.write_text(gt.model_dump_json(indent=2), encoding="utf-8")
        print(f"Wrote {out} -> {gt.overall_verdict.value}")


if __name__ == "__main__":
    data_root = ROOT / "data" / "cases"
    write_all(data_root)
