# AntennaProof Evaluation Report

## Summary

| Metric | Baseline | Agentic | Change |
|--------|----------|---------|--------|
| Correct Verdict Rate | 66.7% | 100.0% | +33.3% |
| Mean Metric Accuracy | 88.9% | 96.1% | +7.2% |
| False PASS Count | 3 | 0 | -3 |
| Unsupported Claims | 62 | 0 | -62 |

## Per-Case Results

| Case | Ground Truth | Baseline | Agentic | Baseline OK | Agentic OK |
|------|--------------|----------|---------|-------------|------------|
| C01 | PASS | PASS | PASS | ✓ | ✓ |
| C02 | PASS | PASS | PASS | ✓ | ✓ |
| C03 | FAIL | FAIL | FAIL | ✓ | ✓ |
| C04 | FAIL | FAIL | FAIL | ✓ | ✓ |
| C05 | INSUFFICIENT_EVIDENCE | INSUFFICIENT_EVIDENCE | INSUFFICIENT_EVIDENCE | ✓ | ✓ |
| C06 | INSUFFICIENT_EVIDENCE | FAIL | INSUFFICIENT_EVIDENCE | ✗ | ✓ |
| C07 | PASS | PASS | PASS | ✓ | ✓ |
| C08 | INSUFFICIENT_EVIDENCE | FAIL | INSUFFICIENT_EVIDENCE | ✗ | ✓ |
| C09 | FAIL | PASS | FAIL | ✗ | ✓ |
| C10 | FAIL | FAIL | FAIL | ✓ | ✓ |
| C11 | PASS | PASS | PASS | ✓ | ✓ |
| C12 | FAIL | FAIL | FAIL | ✓ | ✓ |
| C13 | INSUFFICIENT_EVIDENCE | PASS | INSUFFICIENT_EVIDENCE | ✗ | ✓ |
| C14 | INSUFFICIENT_EVIDENCE | INSUFFICIENT_EVIDENCE | INSUFFICIENT_EVIDENCE | ✓ | ✓ |
| C15 | FAIL | FAIL | FAIL | ✓ | ✓ |
| H01 | INSUFFICIENT_EVIDENCE | PASS | INSUFFICIENT_EVIDENCE | ✗ | ✓ |
| H02 | FAIL | INSUFFICIENT_EVIDENCE | FAIL | ✗ | ✓ |
| H03 | FAIL | FAIL | FAIL | ✓ | ✓ |
