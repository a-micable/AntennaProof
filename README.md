# AntennaProof

**Proof before PASS — an engineering review agent that cannot approve a design without traceable evidence.**

AntennaProof reviews antenna simulation exports and produces **PASS / FAIL / INSUFFICIENT_EVIDENCE** verdicts. A dedicated **Verifier** agent blocks any PASS that lacks a cited `evidence_id` from structured measurements — notes and metadata alone are not enough.

---

## Core Claim

> **An engineering AI should not be allowed to say PASS unless it can prove the verdict using traceable evidence.**

The baseline says PASS from a single script. AntennaProof **rejects, retries evidence collection, or abstains** until every mandatory PASS/FAIL cites simulation exports — or it refuses to approve.

---

## The User

RF engineers reviewing simulation results before fabrication.

## Why Agents (Not One Function)

| Agent | Decision it makes |
|-------|-------------------|
| **Requirements Analyst** | Which metrics are mandatory vs optional |
| **Evidence Extractor** | **Which tools to invoke** (JSON only → +S11 → +notes) by phase |
| **Design Reviewer** | Judgment from **evidence items only** — never reads gold labels |
| **Verifier** | **APPROVE / RETRY_EVIDENCE / ABSTAIN** — changes workflow path |

Deterministic engineering tools (`read_measurements_json`, `analyze_s11_csv`, `detect_resonance_count`, `parse_notes_gain`) are **invoked by the Evidence Extractor**, not hidden inside a monolith.

## Workflow Routing (Verifier-Driven)

```
Phase 1: measurements.json only → Review → Verifier
              ↓ RETRY_EVIDENCE (missing S11 / gain cross-check)
Phase 2: + S11 tools              → Review → Verifier
              ↓ RETRY_EVIDENCE (notes not yet parsed)
Phase 3: + notes parser           → Review → Verifier
              ↓ APPROVE or ABSTAIN (block unsupported PASS)
         design_review.md
```

Example: **C09** triggers `RETRY_EVIDENCE` at phase 1 (incomplete without S11), then detects dual resonance at phase 2 → **FAIL**.

## Independence from Gold Labels

- **Workflow code never imports** `evaluation.rules` or `gold_labeler`
- **Design Reviewer** uses `review_from_evidence.py` (evidence + criteria only)
- **Eval loads committed** `ground_truth.json` — not recomputed from workflow
- Gold labeler (`scripts/gold_labeler`) is a separate reference used only to regenerate labels

## Evaluation

### Primary suite (15 cases)

| Metric | Baseline | Agentic | Change |
|--------|----------|---------|--------|
| **Correct Verdict Rate** | 73.3% | **100.0%** | **+26.7%** |
| False PASS | 2 | 0 | -2 |
| Unsupported claims | 54 | 0 | -54 |

### Holdout adversarial (+3 cases, `--holdout`)

| Case | Trap | Expected |
|------|------|----------|
| H01 | Gain only in notes | INSUFFICIENT_EVIDENCE |
| H02 | Empty JSON, S11 only | FAIL (no gain) |
| H03 | Metadata says PASS | FAIL (bandwidth 78 MHz) |

Run: `./scripts/run_evaluation.sh` or `python3 -m src.main evaluate --holdout`

## Hot Take

> **Verification routing beat smarter judgment.** Forcing `RETRY_EVIDENCE` when S11 tools were not yet invoked fixed more cases than tuning review prompts. The verifier mattered more than adding agents.

## Reproduction

```bash
pip install -r requirements.txt
pytest -q                              # 25 tests incl. leakage + holdout
./scripts/run_evaluation.sh
python3 -m src.main run --case C09_multi_resonance  # see verifier retry in trajectory
```

## Limitations

- No radiation pattern PNG parsing yet
- Deterministic by default (reproducible, $0 eval cost)
- Gold labels regenerated via separate labeler — workflow cannot see that code path

MIT License.
