"""Deterministic engineering tools agents may invoke."""

from __future__ import annotations

import re
from typing import Callable

from src.schemas import EvidenceItem
from src.tools.case_loader import CaseBundle
from src.tools.s11_analyzer import analyze_s11_csv
from src.tools.unit_normalizer import frequencies_conflict, parse_frequency

TOOL_NAMES = (
    "read_measurements_json",
    "analyze_s11_csv",
    "parse_notes_gain",
    "detect_resonance_count",
)


def plan_tools(bundle: CaseBundle, phase: int) -> tuple[list[str], str]:
    """Agent decision: which tools to run at this extraction phase."""
    if phase <= 1:
        selected = ["read_measurements_json"]
        return selected, "Phase 1: structured simulation exports only."
    if phase == 2:
        selected = ["read_measurements_json"]
        if bundle.s11_path:
            selected.extend(["analyze_s11_csv", "detect_resonance_count"])
        rationale = "Phase 2: expand to S11 sweep tools after verifier rejection."
        return selected, rationale
    selected = ["read_measurements_json"]
    if bundle.s11_path:
        selected.extend(["analyze_s11_csv", "detect_resonance_count"])
    if bundle.notes.strip():
        selected.append("parse_notes_gain")
    return selected, "Phase 3: include narrative notes for disputed metrics."


def invoke_tools(bundle: CaseBundle, tool_names: list[str]) -> list[EvidenceItem]:
    evidence: list[EvidenceItem] = []
    idx = 1

    def add(metric: str, value: float | str | None, unit: str, source: str, quote: str = "", tool: str = ""):
        nonlocal idx
        if value is None:
            return
        evidence.append(
            EvidenceItem(
                evidence_id=f"E{idx:02d}",
                metric=metric,
                value=value,
                unit=unit,
                source=source,
                quote=quote or f"tool={tool}",
                confidence="high" if source == "measurements.json" else "medium",
            )
        )
        idx += 1

    if "read_measurements_json" in tool_names:
        meas = bundle.measurements
        add("resonant_frequency", meas.get("resonant_frequency_ghz"), "GHz", "measurements.json", tool="read_measurements_json")
        if meas.get("resonant_frequency_mhz") is not None:
            add("resonant_frequency", meas.get("resonant_frequency_mhz"), "MHz", "measurements.json", tool="read_measurements_json")
        add("bandwidth", meas.get("bandwidth_mhz"), "MHz", "measurements.json", tool="read_measurements_json")
        add("peak_gain", meas.get("peak_gain_dbi"), "dBi", "measurements.json", tool="read_measurements_json")
        add("minimum_s11", meas.get("minimum_s11_db", meas.get("min_s11_db")), "dB", "measurements.json", tool="read_measurements_json")
        add("efficiency", meas.get("efficiency_percent"), "%", "measurements.json", tool="read_measurements_json")
        add("peak_directivity", meas.get("peak_directivity_dbi"), "dBi", "measurements.json", tool="read_measurements_json")

    if "analyze_s11_csv" in tool_names and bundle.s11_path:
        s11 = analyze_s11_csv(bundle.s11_path)
        add("resonant_frequency", s11.resonant_frequency_ghz, "GHz", "s11.csv", "S11 minimum", "analyze_s11_csv")
        add("bandwidth", s11.bandwidth_mhz, "MHz", "s11.csv", "At -10 dB threshold", "analyze_s11_csv")
        add("minimum_s11", s11.minimum_s11_db, "dB", "s11.csv", "Sweep minimum", "analyze_s11_csv")

    if "detect_resonance_count" in tool_names and bundle.s11_path:
        s11 = analyze_s11_csv(bundle.s11_path)
        add("resonance_count", float(s11.resonance_count), "count", "s11.csv", "; ".join(s11.notes), "detect_resonance_count")

    if "parse_notes_gain" in tool_names and bundle.notes:
        m = re.search(r"(\d+(?:\.\d+)?)\s*dBi", bundle.notes, re.I)
        if m:
            add("peak_gain_claimed", float(m.group(1)), "dBi", "notes.txt", bundle.notes[:120], "parse_notes_gain")

    return evidence
