#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
CASE="${1:-C03_bandwidth_fail}"
python3 -m src.main run --case "$CASE" --output results/agentic
echo "Results in results/agentic/$CASE/"
