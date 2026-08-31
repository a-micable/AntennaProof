"""Gold labels — independent reference implementation (NOT imported by agents)."""

from __future__ import annotations

# Re-export labeler used ONLY by scripts/tests that regenerate committed gold JSON.
from src.evaluation.rules import evaluate_to_ground_truth as compute_gold_from_case  # noqa: F401
