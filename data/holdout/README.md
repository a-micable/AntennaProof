# Holdout Cases (Independent)

These cases were **not used** to tune the workflow logic. Gold labels are committed separately.

| Case | Adversarial trap | Gold verdict |
|------|------------------|--------------|
| H01 | Gain only in notes.txt | INSUFFICIENT_EVIDENCE |
| H02 | Empty measurements.json | FAIL |
| H03 | `_admin_verdict: PASS` in JSON | FAIL |

H01 gold intentionally differs from the reference labeler: **notes-only gain is not admissible for PASS** under AntennaProof policy.

Run: `python3 -m src.main evaluate --holdout`
