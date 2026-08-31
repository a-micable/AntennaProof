"""Workflow state passed between agents."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from src.schemas import AcceptanceCriteria, EvidenceItem, ProposedReview, VerifiedReview


class VerifierAction(str, Enum):
    APPROVE = "APPROVE"
    RETRY_EVIDENCE = "RETRY_EVIDENCE"
    ABSTAIN = "ABSTAIN"


class ExtractionPlan(BaseModel):
    phase: int = 1
    tools_selected: list[str] = Field(default_factory=list)
    rationale: str = ""


class ExtractionResult(BaseModel):
    plan: ExtractionPlan
    evidence: list[EvidenceItem] = Field(default_factory=list)


class VerifierDecision(BaseModel):
    action: VerifierAction
    approved: bool
    review: ProposedReview | None = None
    violations: list[str] = Field(default_factory=list)


class WorkflowState(BaseModel):
    case_id: str
    criteria: AcceptanceCriteria | None = None
    extraction_phase: int = 1
    extraction_history: list[ExtractionResult] = Field(default_factory=list)
    proposed_review: ProposedReview | None = None
    verifier_decisions: list[VerifierDecision] = Field(default_factory=list)
    final_review: ProposedReview | None = None
    verified: VerifiedReview | None = None
