"""Design Reviewer — compares evidence against criteria (never reads gold labeler)."""

from __future__ import annotations

from src.agents.review_from_evidence import review_from_evidence
from src.schemas import AcceptanceCriteria, EvidenceItem, ProposedReview
from src.tools.case_loader import CaseBundle


def review_design(
    criteria: AcceptanceCriteria,
    evidence: list[EvidenceItem],
    bundle: CaseBundle | None = None,
) -> ProposedReview:
    fail_on_multi = bool(bundle and bundle.requirements.get("fail_on_multi_resonance"))
    return review_from_evidence(criteria, evidence, fail_on_multi_resonance=fail_on_multi)
