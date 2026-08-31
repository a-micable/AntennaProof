"""Requirements Analyst — converts specs into measurable acceptance criteria."""

from __future__ import annotations

from src.schemas import AcceptanceCriteria, CriterionSpec
from src.tools.case_loader import CaseBundle


def _normalize_metric(name: str) -> str:
    if name in ("min_s11", "minimum_s11"):
        return "minimum_s11"
    return name


def analyze_requirements(bundle: CaseBundle) -> AcceptanceCriteria:
    req = bundle.requirements
    raw = req.get("criteria", {})
    mandatory = [_normalize_metric(m) for m in req.get("mandatory_metrics", [])]
    optional = [_normalize_metric(m) for m in req.get("optional_metrics", [])]

    criteria: list[CriterionSpec] = []

    if "resonant_frequency" in raw or "resonant_frequency" in mandatory:
        c = raw.get("resonant_frequency", {})
        criteria.append(
            CriterionSpec(
                metric="resonant_frequency",
                description="Resonant frequency within band",
                operator="in_range",
                min_value=c.get("min_ghz"),
                max_value=c.get("max_ghz"),
                unit="GHz",
                mandatory="resonant_frequency" in mandatory,
            )
        )

    if "bandwidth" in raw or "bandwidth" in mandatory:
        c = raw.get("bandwidth", {})
        criteria.append(
            CriterionSpec(
                metric="bandwidth",
                description="Impedance bandwidth at S11 threshold",
                operator="gte",
                value=c.get("min_mhz"),
                unit="MHz",
                mandatory="bandwidth" in mandatory,
            )
        )

    if "peak_gain" in raw or "peak_gain" in mandatory:
        c = raw.get("peak_gain", {})
        criteria.append(
            CriterionSpec(
                metric="peak_gain",
                description="Peak realized gain",
                operator="gte",
                value=c.get("min_dbi"),
                unit="dBi",
                mandatory="peak_gain" in mandatory,
            )
        )

    s11_key = "minimum_s11" if "minimum_s11" in raw else "min_s11"
    if s11_key in raw or "minimum_s11" in mandatory or "min_s11" in mandatory:
        c = raw.get(s11_key, {})
        criteria.append(
            CriterionSpec(
                metric="minimum_s11",
                description="Minimum S11 across band",
                operator="lte",
                value=c.get("max_db"),
                unit="dB",
                mandatory="minimum_s11" in mandatory or "min_s11" in mandatory,
            )
        )

    if "efficiency" in raw or "efficiency" in mandatory or "efficiency" in optional:
        c = raw.get("efficiency", {})
        criteria.append(
            CriterionSpec(
                metric="efficiency",
                description="Radiation efficiency",
                operator="gte",
                value=c.get("min_percent"),
                unit="%",
                mandatory="efficiency" in mandatory,
            )
        )

    return AcceptanceCriteria(
        case_id=bundle.case_id,
        design_name=req.get("design_name", req.get("title", bundle.case_id)),
        criteria=criteria,
        mandatory_metrics=mandatory,
        optional_metrics=optional,
    )
