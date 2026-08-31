"""AntennaProof orchestrator — stateful multi-agent workflow with verifier routing."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from src.agents.design_reviewer import review_design
from src.agents.evidence_extractor import extract_evidence
from src.agents.report_assembler import assemble_report
from src.agents.requirements_analyst import analyze_requirements
from src.agents.verifier import verify_review
from src.schemas import ProposedReview
from src.state.workflow_state import VerifierAction, WorkflowState
from src.tools.case_loader import CaseBundle, load_case


@dataclass
class WorkflowResult:
    case_id: str
    review: ProposedReview
    verified: object
    report_markdown: str
    trajectory: dict = field(default_factory=dict)
    state: WorkflowState | None = None


def run_workflow(bundle: CaseBundle, max_phases: int = 3) -> WorkflowResult:
    state = WorkflowState(case_id=bundle.case_id)
    trajectory: dict = {
        "case_id": bundle.case_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "transitions": [],
    }

    criteria = analyze_requirements(bundle)
    state.criteria = criteria
    trajectory["transitions"].append({"step": "RequirementsAnalyst", "output": "AcceptanceCriteria compiled"})

    phase = 1
    proposed: ProposedReview | None = None
    decision = None
    verification_log: list[str] = []

    while phase <= max_phases:
        extraction = extract_evidence(bundle, phase=phase)
        state.extraction_history.append(extraction)
        trajectory["transitions"].append(
            {
                "step": "EvidenceExtractor",
                "phase": phase,
                "tools_selected": extraction.plan.tools_selected,
                "rationale": extraction.plan.rationale,
                "evidence_count": len(extraction.evidence),
            }
        )

        proposed = review_design(criteria, extraction.evidence, bundle)
        state.proposed_review = proposed
        trajectory["transitions"].append(
            {
                "step": "DesignReviewer",
                "phase": phase,
                "proposed_verdict": proposed.overall_verdict.value,
                "decision_basis": "evidence_items_only",
            }
        )

        decision = verify_review(
            proposed,
            extraction.evidence,
            criteria.mandatory_metrics,
            extraction_phase=phase,
            max_phase=max_phases,
            has_s11=bundle.s11_path is not None,
            has_notes=bool(bundle.notes.strip()),
        )
        state.verifier_decisions.append(decision)
        trajectory["transitions"].append(
            {
                "step": "Verifier",
                "phase": phase,
                "action": decision.action.value,
                "violations": decision.violations,
                "approved": decision.approved,
            }
        )

        if decision.action == VerifierAction.APPROVE:
            break
        if decision.action == VerifierAction.RETRY_EVIDENCE:
            verification_log.append(
                f"Phase {phase}: verifier rejected — retry evidence collection ({'; '.join(decision.violations[:2])})"
            )
            phase += 1
            continue
        if decision.action == VerifierAction.ABSTAIN:
            verification_log.append(f"Phase {phase}: verifier abstains — INSUFFICIENT_EVIDENCE")
            proposed = decision.review
            break

    final = decision.review if decision and decision.review else proposed
    state.final_review = final

    from src.schemas import VerifiedReview

    verified = VerifiedReview(approved=decision.approved if decision else False, review=final, violations=decision.violations if decision else [])
    state.verified = verified

    design_name = criteria.design_name or bundle.case_id
    report = assemble_report(bundle.case_id, design_name, verified, verification_log)
    trajectory["transitions"].append({"step": "ReportAssembler", "final_verdict": final.overall_verdict.value if final else None})
    trajectory["final_phase"] = phase

    return WorkflowResult(
        case_id=bundle.case_id,
        review=final or proposed,
        verified=verified,
        report_markdown=report,
        trajectory=trajectory,
        state=state,
    )


def run_case(case_dir: Path, output_dir: Path | None = None) -> WorkflowResult:
    bundle = load_case(case_dir)
    result = run_workflow(bundle)

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "design_review.md").write_text(result.report_markdown, encoding="utf-8")
        (output_dir / "trajectory.json").write_text(json.dumps(result.trajectory, indent=2), encoding="utf-8")
        if result.state:
            (output_dir / "workflow_state.json").write_text(result.state.model_dump_json(indent=2), encoding="utf-8")
        if result.review:
            (output_dir / "review.json").write_text(result.review.model_dump_json(indent=2), encoding="utf-8")

    return result
