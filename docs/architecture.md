# Architecture

See [README.md](../README.md) for overview.

## Components

| Layer | Module | Purpose |
|-------|--------|---------|
| Tools | `src/tools/s11_analyzer.py` | Deterministic bandwidth/resonance from S11 CSV |
| Tools | `src/tools/unit_normalizer.py` | GHz/MHz parsing and conflict detection |
| Rules | `src/evaluation/rules.py` | Shared PASS/FAIL/IE logic for reviewer + gold labels |
| Agent | `src/agents/requirements_analyst.py` | Spec → acceptance criteria |
| Agent | `src/agents/evidence_extractor.py` | Case files → evidence list |
| Agent | `src/agents/design_reviewer.py` | Evidence vs criteria → proposed review |
| Agent | `src/agents/verifier.py` | Block unsupported conclusions |
| Agent | `src/agents/report_assembler.py` | Markdown report |
| Workflow | `src/workflows/orchestrator.py` | End-to-end pipeline + trajectory logging |
| Baseline | `baseline/baseline.py` | Single-pass comparison system |

## Design Decisions

1. **Hybrid deterministic + agent modular pipeline** — numeric checks are code, not LLM guesses.
2. **Verifier before report** — PASS requires evidence_id on every mandatory metric.
3. **FAIL beats IE** — confirmed threshold breach yields FAIL even if another metric is ambiguous.
4. **Optional metrics never affect overall verdict** — only mandatory metrics drive PASS/FAIL/IE.
