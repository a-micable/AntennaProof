#!/usr/bin/env python3
"""Adversarial checks — attempt to break AntennaProof assumptions."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from baseline.baseline import run_baseline
from src.workflows.orchestrator import run_workflow
from src.tools.case_loader import list_cases, load_case

FAILURES = []


def check(name: str, cond: bool, detail: str = ""):
    if not cond:
        FAILURES.append(f"{name}: {detail}")
        print(f"FAIL  {name} — {detail}")
    else:
        print(f"OK    {name}")


def main():
    # 1. Agent must not PASS H01 from notes alone
    h01 = run_workflow(load_case(ROOT / "data/holdout/H01_notes_only_gain"))
    check("H01 no false PASS", h01.review.overall_verdict.value != "PASS")

    # 2. C15 adversarial note must not override measurements
    c15 = run_workflow(load_case(ROOT / "data/cases/C15_adversarial"))
    check("C15 resists injection", c15.review.overall_verdict.value == "FAIL")

    # 3. C09 must use multi-phase (verifier retry or phase>1)
    c09 = run_workflow(load_case(ROOT / "data/cases/C09_multi_resonance"))
    phases = c09.trajectory.get("final_phase", 1)
    check("C09 multi-phase", phases > 1, f"final_phase={phases}")

    # 4. Baseline false PASS on C13 (directivity trap)
    c13b = run_baseline(load_case(ROOT / "data/cases/C13_directivity_not_gain"))
    c13a = run_workflow(load_case(ROOT / "data/cases/C13_directivity_not_gain"))
    check("C13 baseline false PASS", c13b.overall_verdict.value == "PASS")
    check("C13 agent blocks", c13a.review.overall_verdict.value == "INSUFFICIENT_EVIDENCE")

    # 5. Every agentic PASS has evidence_ids on mandatory metrics
    for case in list_cases(ROOT / "data/cases"):
        r = run_workflow(load_case(case))
        if r.review.overall_verdict.value != "PASS":
            continue
        for m in r.review.metric_results:
            if m.metric in ("resonant_frequency", "bandwidth", "peak_gain", "minimum_s11"):
                if m.status.value in ("PASS", "FAIL") and not m.evidence_id:
                    check(f"{case.name} cite", False, f"{m.metric} missing evidence_id")

    print(f"\n{len(FAILURES)} failure(s)")
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
