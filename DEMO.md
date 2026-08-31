# AntennaProof — Final 5-Minute Recording Guide

**Narrative:** C13 false PASS → architecture → C13 blocked → C09 retry → C06 conflict → eval → changelog → pytest → close.

Screen-record from `/home/amicable/HAck_micro1`. Terminal font 18–20pt. Hide notifications.

**Total runtime target:** ~4:30 (comfortable buffer under 5:00).

---

## Pre-open in editor (before recording)

Have these tabs ready — switch to them, do not navigate during recording:

1. `data/cases/C13_directivity_not_gain/measurements.json`
2. `docs/demo_architecture.md`
3. `results/agentic/C13_directivity_not_gain/design_review.md`
4. `CHANGELOG.md` (scroll to **Removed Experiment** at bottom, lines 75–83)
5. `docs/demo_results.md` (backup if eval command fails)

---

## FINAL RECORDING ORDER

### STEP 1 — C13 baseline false PASS · 0:00–0:25

**Say (15 sec):**  
“RF engineers review antenna simulations before fabrication. Here is a real export — it reports peak **directivity**, not peak **gain**. A single-pass reviewer can still say PASS.”

**Show (editor, 5 sec):** `measurements.json` — point at `"peak_directivity_dbi": 6.5`, no `peak_gain_dbi`.

**Terminal:**
```bash
cd /home/amicable/HAck_micro1
python3 -m src.main baseline --case C13_directivity_not_gain
```

**Expected:**
```
PASS
```

**Say (5 sec):** “False PASS. No verifier. No evidence citation.”

---

### STEP 2 — Architecture · 0:25–1:00

**Show (editor, 30 sec):** `docs/demo_architecture.md`

**Say:**  
“We separate four decisions on purpose. **Requirements** — what is mandatory. **Evidence** — what tools to run and what facts to extract. **Judgment** — PASS, FAIL, or insufficient evidence from facts only. **Verification** — block or retry before any verdict is final. Judgment cannot run ahead of evidence, and PASS cannot survive without proof.”

**Do not** open `src/` code.

---

### STEP 3 — C13 AntennaProof blocks · 1:00–1:40

**Terminal:**
```bash
python3 scripts/demo_runner.py c13
```

**Expected:**
```
  Baseline: PASS
  Agentic:  INSUFFICIENT_EVIDENCE
```

**Show (editor, 15 sec):** `results/agentic/C13_directivity_not_gain/design_review.md`

**Highlight this line:**
```
- **peak_gain:** Only directivity reported; gain required.
```

**Say:** “AntennaProof blocks the unsupported conclusion. INSUFFICIENT_EVIDENCE — not a guessed PASS.”

---

### STEP 4 — C09 verifier retry · 1:40–2:30

**Terminal:**
```bash
python3 scripts/demo_runner.py c09
```

**Expected (key lines):**
```
  Baseline: PASS
  Agentic:  FAIL
    Phase 1: Verifier → RETRY_EVIDENCE
              reason: Mandatory metrics missing — invoke S11 tools
    Phase 2: Evidence Extractor → read_measurements_json, analyze_s11_csv, detect_resonance_count
    Phase 2: Design Reviewer → FAIL
    Phase 2: Verifier → APPROVE
```

**Say:** “Phase 1 evidence was incomplete. The verifier did not approve — it routed back to extraction. Phase 2 invoked S11 tools, detected dual resonance, and returned FAIL. This is agentic routing, not one monolithic script.”

---

### STEP 5 — C06 conflicting evidence · 2:30–3:05

**Terminal:**
```bash
python3 scripts/demo_runner.py c06
```

**Expected:**
```
  Baseline: FAIL
  Agentic:  INSUFFICIENT_EVIDENCE
  notes claim 6.0 dBi; measurements.json reports 4.2 dBi
```

**Show (editor, 10 sec):** `notes.txt` vs `measurements.json` side by side.

**Say:** “Conflicting sources. The workflow returns INSUFFICIENT_EVIDENCE — it does not pick a winner and call it PASS.”

---

### STEP 6 — Measured evaluation · 3:05–3:45

**Terminal:**
```bash
python3 scripts/demo_runner.py eval
```

**Expected table:**
```
| Correct Verdict Rate | 73.3% | 100.0% | +26.7% |
| False PASS Count     | 2     | 0      | -2     |
| Unsupported Claims   | 54    | 0      | -54    |
```

**Say:** “Same fifteen cases, identical inputs. Baseline: seventy-three point three percent correct verdict rate, two false PASSes, fifty-four unsupported claims. AntennaProof: one hundred percent, zero, zero.”

---

### STEP 7 — Changelog: removed critic · 3:45–4:15

**Show (editor, 20 sec):** `CHANGELOG.md` lines 75–83:

```
What was attempted: Extra agent to re-review the reviewer's rationale.
What evaluation revealed: Identical CVR to 4-agent pipeline; +40% latency.
Why removed: Coordination cost with zero measurable gain.
Lesson (Hot Take): Verification > more agents.
```

**Say:** “We tested a fifth critic agent. Evaluation showed identical correct verdict rate and forty percent more latency. We removed it. Verification routing beat adding agents.”

---

### STEP 8 — Pytest reproducibility · 4:15–4:35

**Terminal:**
```bash
pytest -q
```

**Expected:**
```
25 passed in 0.3s
```

**Say:** “Twenty-five tests. No API key. Deterministic. Zero dollar evaluation cost.”

---

### STEP 9 — Final message · 4:35–5:00

**Say (look at camera or terminal):**  
“A system should not be allowed to say PASS unless it can prove why. AntennaProof — proof before PASS.”

**Optional freeze frame:** `docs/demo_architecture.md` or README tagline.

---

## Command cheat sheet (copy-paste order)

```bash
cd /home/amicable/HAck_micro1
python3 -m src.main baseline --case C13_directivity_not_gain
python3 scripts/demo_runner.py c13
python3 scripts/demo_runner.py c09
python3 scripts/demo_runner.py c06
python3 scripts/demo_runner.py eval
pytest -q
```

**Not in the 5-min cut:** C03, C15, `./scripts/run_demo.sh`, Docker, source code.

---

## Do NOT show

- `src/` Python files
- `.env.example`
- C09 second baseline run (C13 already proves false PASS)
- C15 adversarial (cut for time)
- `trajectories/C03_trajectory.json` (stale schema)
- Orphan case folders
- Full pytest dots (only final `25 passed` line)
- `generate-ground-truth`

---

## Pre-recording verification (run once)

```bash
cd /home/amicable/HAck_micro1
python3 -m src.main baseline --case C13_directivity_not_gain   # → PASS
python3 scripts/demo_runner.py c13                             # → PASS / IE
python3 scripts/demo_runner.py c09                             # → RETRY_EVIDENCE
python3 scripts/demo_runner.py c06                             # → IE
python3 scripts/demo_runner.py eval                            # → 73.3% → 100%
pytest -q                                                        # → 25 passed
```

All commands verified before this guide was written.
