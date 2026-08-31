#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
CASE="${1:-C03_bandwidth_fail}"
python3 -m src.main baseline --case "$CASE" --output results/baseline
