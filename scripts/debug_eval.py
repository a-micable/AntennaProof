#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from baseline.baseline import run_baseline
from src.tools.case_loader import load_case, list_cases
from src.workflows.orchestrator import run_workflow
from src.evaluation.ground_truth import compute_ground_truth

data = ROOT / "data" / "cases"
for case_dir in list_cases(data):
    bundle = load_case(case_dir)
    gt = compute_ground_truth(bundle)
    agent = run_workflow(bundle)
    base = run_baseline(bundle)
    av = agent.verified.review.overall_verdict if agent.verified.review else None
    ok = "OK" if av == gt.overall_verdict else "MISS"
    print(f"{bundle.case_id}: gold={gt.overall_verdict.value} base={base.overall_verdict.value} agent={av.value if av else None} {ok}")
