"""Evidence Extractor — selects tools and collects facts (no pass/fail)."""

from __future__ import annotations

from src.schemas import EvidenceItem
from src.state.workflow_state import ExtractionPlan, ExtractionResult
from src.tools.case_loader import CaseBundle
from src.tools.engineering_tools import invoke_tools, plan_tools


def extract_evidence(bundle: CaseBundle, phase: int = 1) -> ExtractionResult:
    tools, rationale = plan_tools(bundle, phase)
    evidence = invoke_tools(bundle, tools)
    return ExtractionResult(
        plan=ExtractionPlan(phase=phase, tools_selected=tools, rationale=rationale),
        evidence=evidence,
    )
