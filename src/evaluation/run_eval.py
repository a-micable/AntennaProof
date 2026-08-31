"""Evaluation harness — compare baseline vs agentic workflow."""

from __future__ import annotations

import json
from pathlib import Path

from baseline.baseline import run_baseline
from src.evaluation.ground_truth import compute_ground_truth
from src.schemas import EvaluationCaseResult, EvaluationReport, MetricStatus, OverallVerdict
from src.tools.case_loader import list_cases, load_case
from src.workflows.orchestrator import run_workflow


def _load_ground_truth(bundle) -> OverallVerdict:
    gt_path = bundle.case_dir / "ground_truth.json"
    if gt_path.exists():
        data = json.loads(gt_path.read_text(encoding="utf-8"))
        return OverallVerdict(data["overall_verdict"])
    return compute_ground_truth(bundle).overall_verdict


def _metric_accuracy(predicted, ground_truth_metrics: dict) -> float:
    if not predicted.metric_results:
        return 0.0
    correct = 0
    total = 0
    for pr in predicted.metric_results:
        gt_status = ground_truth_metrics.get(pr.metric)
        if gt_status is None:
            continue
        total += 1
        if pr.status.value == gt_status:
            correct += 1
    return correct / total if total else 0.0


def _unsupported_claims(predicted) -> int:
    count = 0
    for pr in predicted.metric_results:
        if pr.status in (MetricStatus.PASS, MetricStatus.FAIL):
            if not pr.evidence_id and pr.measured is not None:
                count += 1
    return count


def evaluate_system(system: str, data_root: Path, holdout_root: Path | None = None) -> EvaluationReport:
    per_case: list[EvaluationCaseResult] = []
    case_dirs = list_cases(data_root)
    if holdout_root and holdout_root.exists():
        case_dirs = case_dirs + list_cases(holdout_root)
    for case_dir in case_dirs:
        bundle = load_case(case_dir)
        gt = compute_ground_truth(bundle)
        gt_metrics = {m.metric: m.status.value for m in gt.metrics}
        gt_verdict = gt.overall_verdict

        if system == "baseline":
            predicted = run_baseline(bundle)
        elif system == "agentic":
            result = run_workflow(bundle)
            predicted = result.verified.review or result.review
        else:
            raise ValueError(f"Unknown system: {system}")

        pred_verdict = predicted.overall_verdict if predicted else None
        verdict_correct = pred_verdict == gt_verdict if pred_verdict else False
        false_pass = (
            pred_verdict == OverallVerdict.PASS
            and gt_verdict != OverallVerdict.PASS
        )

        per_case.append(
            EvaluationCaseResult(
                case_id=bundle.case_id,
                predicted_verdict=pred_verdict,
                ground_truth_verdict=gt_verdict,
                verdict_correct=verdict_correct,
                metric_accuracy=_metric_accuracy(predicted, gt_metrics),
                unsupported_claims=_unsupported_claims(predicted),
                false_pass=false_pass,
            )
        )

    total = len(per_case)
    return EvaluationReport(
        system=system,
        total_cases=total,
        correct_verdict_rate=sum(1 for c in per_case if c.verdict_correct) / total if total else 0,
        mean_metric_accuracy=sum(c.metric_accuracy for c in per_case) / total if total else 0,
        false_pass_count=sum(1 for c in per_case if c.false_pass),
        unsupported_claims_total=sum(c.unsupported_claims for c in per_case),
        per_case=per_case,
    )


def compare_systems(data_root: Path, holdout_root: Path | None = None) -> dict:
    baseline = evaluate_system("baseline", data_root, holdout_root)
    agentic = evaluate_system("agentic", data_root, holdout_root)
    return {
        "baseline": json.loads(baseline.model_dump_json()),
        "agentic": json.loads(agentic.model_dump_json()),
        "comparison": {
            "correct_verdict_rate": {
                "baseline": baseline.correct_verdict_rate,
                "agentic": agentic.correct_verdict_rate,
                "change": agentic.correct_verdict_rate - baseline.correct_verdict_rate,
            },
            "false_pass_count": {
                "baseline": baseline.false_pass_count,
                "agentic": agentic.false_pass_count,
                "change": agentic.false_pass_count - baseline.false_pass_count,
            },
            "unsupported_claims_total": {
                "baseline": baseline.unsupported_claims_total,
                "agentic": agentic.unsupported_claims_total,
                "change": agentic.unsupported_claims_total - baseline.unsupported_claims_total,
            },
            "mean_metric_accuracy": {
                "baseline": baseline.mean_metric_accuracy,
                "agentic": agentic.mean_metric_accuracy,
                "change": agentic.mean_metric_accuracy - baseline.mean_metric_accuracy,
            },
        },
    }


def write_eval_report(data_root: Path, output_path: Path, holdout_root: Path | None = None) -> dict:
    results = compare_systems(data_root, holdout_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# AntennaProof Evaluation Report",
        "",
        "## Summary",
        "",
        "| Metric | Baseline | Agentic | Change |",
        "|--------|----------|---------|--------|",
    ]
    comp = results["comparison"]
    lines.append(
        f"| Correct Verdict Rate | {comp['correct_verdict_rate']['baseline']:.1%} | "
        f"{comp['correct_verdict_rate']['agentic']:.1%} | "
        f"{comp['correct_verdict_rate']['change']:+.1%} |"
    )
    lines.append(
        f"| Mean Metric Accuracy | {comp['mean_metric_accuracy']['baseline']:.1%} | "
        f"{comp['mean_metric_accuracy']['agentic']:.1%} | "
        f"{comp['mean_metric_accuracy']['change']:+.1%} |"
    )
    lines.append(
        f"| False PASS Count | {comp['false_pass_count']['baseline']} | "
        f"{comp['false_pass_count']['agentic']} | "
        f"{comp['false_pass_count']['change']:+d} |"
    )
    lines.append(
        f"| Unsupported Claims | {comp['unsupported_claims_total']['baseline']} | "
        f"{comp['unsupported_claims_total']['agentic']} | "
        f"{comp['unsupported_claims_total']['change']:+d} |"
    )
    lines.append("")
    lines.append("## Per-Case Results")
    lines.append("")
    lines.append("| Case | Ground Truth | Baseline | Agentic | Baseline OK | Agentic OK |")
    lines.append("|------|--------------|----------|---------|-------------|------------|")

    baseline_cases = {c["case_id"]: c for c in results["baseline"]["per_case"]}
    agentic_cases = {c["case_id"]: c for c in results["agentic"]["per_case"]}

    for case_id in sorted(baseline_cases.keys()):
        b = baseline_cases[case_id]
        a = agentic_cases[case_id]
        gt = b["ground_truth_verdict"]
        if isinstance(gt, str) and gt.startswith("OverallVerdict."):
            gt = gt.replace("OverallVerdict.", "")
        bp = b["predicted_verdict"]
        if isinstance(bp, str) and bp.startswith("OverallVerdict."):
            bp = bp.replace("OverallVerdict.", "")
        ap = a["predicted_verdict"]
        if isinstance(ap, str) and ap.startswith("OverallVerdict."):
            ap = ap.replace("OverallVerdict.", "")
        lines.append(
            f"| {case_id} | {gt} | {bp} | {ap} | "
            f"{'✓' if b['verdict_correct'] else '✗'} | {'✓' if a['verdict_correct'] else '✗'} |"
        )

    md = "\n".join(lines) + "\n"
    output_path.write_text(md, encoding="utf-8")
    json_path = output_path.with_suffix(".json")
    json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results
