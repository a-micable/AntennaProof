# AntennaProof Demo Results

Key metrics from `results/eval_report.md` (15-case primary suite).  
Both systems evaluated on identical case inputs.

## Summary

| Metric | Baseline | Agentic | Change |
|--------|----------|---------|--------|
| Correct Verdict Rate | 73.3% | 100.0% | +26.7% |
| Mean Metric Accuracy | 93.3% | 95.3% | +2.0% |
| False PASS Count | 2 | 0 | -2 |
| Unsupported Claims | 54 | 0 | -54 |

## Baseline failures (agentic correct)

| Case | Ground Truth | Baseline | Agentic | Issue |
|------|--------------|----------|---------|-------|
| C06 | INSUFFICIENT_EVIDENCE | FAIL | INSUFFICIENT_EVIDENCE | Notes vs JSON gain conflict |
| C08 | INSUFFICIENT_EVIDENCE | FAIL | INSUFFICIENT_EVIDENCE | Unit conflict |
| C09 | FAIL | **PASS** | FAIL | Dual-resonance S11 ignored |
| C13 | INSUFFICIENT_EVIDENCE | **PASS** | INSUFFICIENT_EVIDENCE | Directivity treated as gain |

## Demo case verdicts (quick reference)

| Case | Purpose | Baseline | Agentic |
|------|---------|----------|---------|
| C03 | Clear FAIL | FAIL | FAIL |
| C06 | Evidence conflict | FAIL | INSUFFICIENT_EVIDENCE |
| C09 | Verifier retry | PASS | FAIL |
| C13 | False PASS blocked | PASS | INSUFFICIENT_EVIDENCE |
| C15 | Adversarial note | FAIL | FAIL |

## Reproduce

```bash
./scripts/run_evaluation.sh
cat results/eval_report.md
```
