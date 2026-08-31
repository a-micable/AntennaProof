"""Load committed gold labels — eval must not recompute via workflow code."""

from __future__ import annotations

import json
from pathlib import Path

from src.schemas import GroundTruth, GroundTruthMetric, MetricStatus, OverallVerdict
from src.tools.case_loader import CaseBundle, list_cases, load_case, load_case


def load_ground_truth(bundle: CaseBundle) -> GroundTruth:
    if not bundle.ground_truth_path or not bundle.ground_truth_path.exists():
        raise FileNotFoundError(
            f"Missing committed ground_truth.json for {bundle.case_id}. "
            "Run: python3 -m src.main generate-ground-truth"
        )
    data = json.loads(bundle.ground_truth_path.read_text(encoding="utf-8"))
    metrics = [
        GroundTruthMetric(
            metric=m["metric"],
            status=MetricStatus(m["status"]),
            required=m["required"],
            measured=m.get("measured"),
            reason=m.get("reason", ""),
        )
        for m in data["metrics"]
    ]
    return GroundTruth(
        case_id=data["case_id"],
        overall_verdict=OverallVerdict(data["overall_verdict"]),
        metrics=metrics,
        notes=data.get("notes", ""),
    )


def compute_ground_truth(bundle: CaseBundle) -> GroundTruth:
    """Eval harness alias — always loads committed labels."""
    return load_ground_truth(bundle)


def generate_all_ground_truths(data_root: Path) -> None:
    """Regenerate gold JSON using independent labeler (scripts only)."""
    from src.agents.requirements_analyst import analyze_requirements
    from src.evaluation.gold_labeler import compute_gold_from_case

    for case_dir in list_cases(data_root / "cases"):
        bundle = load_case(case_dir)
        criteria = analyze_requirements(bundle)
        gt = compute_gold_from_case(bundle, criteria)
        out = case_dir / "ground_truth.json"
        out.write_text(gt.model_dump_json(indent=2), encoding="utf-8")
        print(f"{bundle.case_id}: {gt.overall_verdict.value}")

    holdout = data_root / "holdout"
    if holdout.exists():
        for case_dir in list_cases(holdout):
            bundle = load_case(case_dir)
            criteria = analyze_requirements(bundle)
            gt = compute_gold_from_case(bundle, criteria)
            out = case_dir / "ground_truth.json"
            out.write_text(gt.model_dump_json(indent=2), encoding="utf-8")
            print(f"{bundle.case_id}: {gt.overall_verdict.value}")
