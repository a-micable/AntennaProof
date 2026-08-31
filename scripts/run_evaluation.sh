#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m src.main evaluate --output results/eval_report.md
cat results/eval_report.md
