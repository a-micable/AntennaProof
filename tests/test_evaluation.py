"""Pytest suite for AntennaProof."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from baseline.baseline import run_baseline
from src.evaluation.ground_truth import load_ground_truth
from src.state.workflow_state import VerifierAction
from src.tools.case_loader import list_cases, load_case
from src.workflows.orchestrator import run_workflow

DATA = ROOT / "data" / "cases"
HOLDOUT = ROOT / "data" / "holdout"

AGENT_MODULES = [
    ROOT / "src" / "agents" / "design_reviewer.py",
    ROOT / "src" / "agents" / "evidence_extractor.py",
    ROOT / "src" / "agents" / "verifier.py",
    ROOT / "src" / "workflows" / "orchestrator.py",
]

FORBIDDEN_IMPORTS = ("evaluation.rules", "evaluation.gold_labeler", "evaluate_bundle", "evaluate_to_ground_truth")


def _imports_in_file(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.append(node.module)
    return out


@pytest.mark.parametrize("module_path", AGENT_MODULES, ids=lambda p: p.name)
def test_agents_do_not_import_gold_labeler(module_path: Path):
    """Prevent answer leakage: workflow must not import gold labeler."""
    imports = _imports_in_file(module_path)
    for imp in imports:
        for forbidden in FORBIDDEN_IMPORTS:
            assert forbidden not in imp, f"{module_path.name} imports gold path: {imp}"


@pytest.mark.parametrize("case_dir", list_cases(DATA), ids=lambda p: p.name)
def test_agentic_matches_committed_ground_truth(case_dir: Path):
    bundle = load_case(case_dir)
    gt = load_ground_truth(bundle)
    result = run_workflow(bundle)
    assert result.review is not None
    assert result.review.overall_verdict == gt.overall_verdict


@pytest.mark.parametrize("case_dir", list_cases(HOLDOUT), ids=lambda p: p.name)
def test_holdout_matches_ground_truth(case_dir: Path):
    bundle = load_case(case_dir)
    gt = load_ground_truth(bundle)
    result = run_workflow(bundle)
    assert result.review.overall_verdict == gt.overall_verdict


def test_verifier_can_retry_evidence_collection():
    """C09 requires phase-2 S11 tools — verifier must route RETRY then approve."""
    bundle = load_case(DATA / "C09_multi_resonance")
    result = run_workflow(bundle)
    actions = [t["action"] for t in result.trajectory["transitions"] if t["step"] == "Verifier"]
    assert VerifierAction.RETRY_EVIDENCE.value in actions or result.trajectory.get("final_phase", 1) > 1


def test_h01_notes_cannot_pass_gain():
    bundle = load_case(HOLDOUT / "H01_notes_only_gain")
    result = run_workflow(bundle)
    gain_rows = [m for m in result.review.metric_results if m.metric == "peak_gain"]
    assert gain_rows and gain_rows[0].status.value != "PASS"


def test_baseline_runs_all_cases():
    for case_dir in list_cases(DATA):
        bundle = load_case(case_dir)
        review = run_baseline(bundle)
        assert review.overall_verdict is not None
