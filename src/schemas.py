"""Pydantic models for AntennaProof."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class MetricStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class OverallVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class CriterionSpec(BaseModel):
    metric: str
    description: str
    operator: str
    value: float | None = None
    min_value: float | None = None
    max_value: float | None = None
    unit: str
    mandatory: bool = True


class AcceptanceCriteria(BaseModel):
    case_id: str
    design_name: str = ""
    criteria: list[CriterionSpec]
    mandatory_metrics: list[str]
    optional_metrics: list[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    evidence_id: str
    metric: str
    value: float | str | None = None
    unit: str
    source: str
    quote: str = ""
    confidence: str = "high"


class MetricResult(BaseModel):
    metric: str
    required: str
    measured: str | None = None
    status: MetricStatus
    evidence_id: str | None = None
    reason: str = ""


class ProposedReview(BaseModel):
    overall_verdict: OverallVerdict
    metric_results: list[MetricResult] = Field(default_factory=list)
    insufficient_evidence: list[str] = Field(default_factory=list)
    confidence: str = "medium"
    evidence_coverage_percent: float = 0.0
    rationale: str = ""


class VerifiedReview(BaseModel):
    approved: bool
    review: ProposedReview | None = None
    violations: list[str] = Field(default_factory=list)


class GroundTruthMetric(BaseModel):
    metric: str
    status: MetricStatus
    required: str
    measured: float | None = None
    reason: str = ""


class GroundTruth(BaseModel):
    case_id: str
    overall_verdict: OverallVerdict
    metrics: list[GroundTruthMetric]
    notes: str = ""


class EvaluationCaseResult(BaseModel):
    case_id: str
    predicted_verdict: OverallVerdict | None = None
    ground_truth_verdict: OverallVerdict
    verdict_correct: bool
    metric_accuracy: float
    unsupported_claims: int = 0
    false_pass: bool = False


class EvaluationReport(BaseModel):
    system: str
    total_cases: int
    correct_verdict_rate: float
    mean_metric_accuracy: float
    false_pass_count: int
    unsupported_claims_total: int
    per_case: list[EvaluationCaseResult]
