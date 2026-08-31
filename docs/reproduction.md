# Reproduction Guide

## Prerequisites

- Python 3.11+
- pip

## Quick Start

```bash
cd HAck_micro1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./scripts/run_evaluation.sh
```

Expected output ends with eval table showing **100% agentic CVR**.

## Individual Commands

```bash
# All tests (18 cases × parametrized + 3 fixed)
pytest -q

# One agent run
python3 -m src.main run --case C03_bandwidth_fail

# Baseline only
python3 -m src.main baseline --case C09_multi_resonance

# Regenerate ground truth
python3 -m src.main generate-ground-truth
```

## Docker

```bash
docker compose up --build
```

Runs evaluation and prints report to stdout.

## Runtime

- Full evaluation: ~2 seconds (deterministic pipeline, no LLM API calls required)
- Cost: $0 for default reproducible path

## Outputs

| Path | Content |
|------|---------|
| `results/eval_report.md` | Baseline vs agentic table |
| `results/agentic/<case>/design_review.md` | Sample review report |
| `results/agentic/<case>/trajectory.json` | Agent decision trace |
| `trajectories/C03_trajectory.json` | Representative PASS/FAIL trace |
