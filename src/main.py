#!/usr/bin/env python3
"""CLI entrypoint for AntennaProof."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from baseline.baseline import run_baseline
from src.evaluation.ground_truth import generate_all_ground_truths
from src.evaluation.run_eval import write_eval_report
from src.tools.case_loader import list_cases, load_case
from src.workflows.orchestrator import run_case


def main() -> None:
    parser = argparse.ArgumentParser(description="AntennaProof — agentic antenna design review")
    sub = parser.add_subparsers(dest="command", required=True)

    gt = sub.add_parser("generate-ground-truth", help="Regenerate ground_truth.json for all cases")
    gt.add_argument("--data", default=str(ROOT / "data"))

    run = sub.add_parser("run", help="Run agentic workflow on one case")
    run.add_argument("--case", required=True, help="Case directory name e.g. C03_bandwidth_fail")
    run.add_argument("--output", default=str(ROOT / "results" / "agentic"))

    base = sub.add_parser("baseline", help="Run baseline on one case")
    base.add_argument("--case", required=True)
    base.add_argument("--output", default=str(ROOT / "results" / "baseline"))

    ev = sub.add_parser("evaluate", help="Compare baseline vs agentic on all cases")
    ev.add_argument("--holdout", action="store_true", help="Include data/holdout cases")
    ev.add_argument("--output", default=str(ROOT / "results" / "eval_report.md"))

    args = parser.parse_args()
    data_root = Path(getattr(args, "data", ROOT / "data"))

    if args.command == "generate-ground-truth":
        generate_all_ground_truths(data_root)
    elif args.command == "run":
        case_dir = data_root / "cases" / args.case
        run_case(case_dir, Path(args.output) / args.case)
        print(f"Wrote results to {args.output}/{args.case}/")
    elif args.command == "baseline":
        case_dir = data_root / "cases" / args.case
        bundle = load_case(case_dir)
        review = run_baseline(bundle)
        out = Path(args.output) / args.case
        out.mkdir(parents=True, exist_ok=True)
        (out / "review.json").write_text(review.model_dump_json(indent=2), encoding="utf-8")
        print(review.overall_verdict.value)
    elif args.command == "evaluate":
        holdout = data_root / "holdout" if args.holdout else None
        write_eval_report(data_root / "cases", Path(args.output), holdout)
        print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
