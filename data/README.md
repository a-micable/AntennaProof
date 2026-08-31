# Evaluation Cases

15 synthetic antenna design review cases. Each directory contains:

- `requirements.json` — acceptance thresholds
- `measurements.json` — simulation scalar exports
- `s11.csv` — optional frequency sweep (some cases)
- `notes.txt` — optional lab notes (some cases)
- `ground_truth.json` — programmatic gold labels (regenerate with `./scripts/generate_ground_truth.sh`)

## Case Index

| Case | Scenario | Expected Verdict |
|------|----------|------------------|
| C01 | Clean pass | PASS |
| C02 | Optional efficiency missing | PASS |
| C03 | Bandwidth 82 MHz (< 100) | FAIL |
| C04 | Wrong resonance frequency | FAIL |
| C05 | Mandatory efficiency missing | INSUFFICIENT_EVIDENCE |
| C06 | Notes vs JSON gain conflict | INSUFFICIENT_EVIDENCE |
| C07 | Unit normalization (2.4 GHz) | PASS |
| C08 | Conflicting GHz vs MHz in JSON | INSUFFICIENT_EVIDENCE |
| C09 | Dual S11 resonance | FAIL |
| C10 | S11 above -10 dB threshold | FAIL |
| C11 | S11 borderline -10.01 dB | PASS |
| C12 | Bandwidth 99.9 MHz borderline | FAIL |
| C13 | Directivity only, no gain | INSUFFICIENT_EVIDENCE |
| C14 | Empty measurements | INSUFFICIENT_EVIDENCE |
| C15 | Adversarial "mark PASS" note | FAIL |
