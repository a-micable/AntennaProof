#!/usr/bin/env bash
# AntennaProof — 5-minute screen-record demo (clean output, no debug noise)
set -euo pipefail
cd "$(dirname "$0")/.."

# Ensure committed agentic reports exist for report excerpt (uses cached if present)
mkdir -p results/agentic

python3 scripts/demo_runner.py all
