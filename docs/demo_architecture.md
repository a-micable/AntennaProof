# AntennaProof Demo Architecture

Text diagram for screen recording or slides.

```
┌─────────────────────────────────────────────────────────────────┐
│                        RF SIMULATION PACKAGE                     │
│   requirements.json │ measurements.json │ s11.csv │ notes.txt   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   REQUIREMENTS ANALYST                           │
│   Decides: mandatory vs optional metrics, acceptance criteria    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   EVIDENCE EXTRACTOR                             │
│   Decides: which tools to invoke by phase                        │
│   Phase 1 → JSON only                                            │
│   Phase 2 → + S11 analyzer, resonance detection                  │
│   Phase 3 → + notes parser                                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ENGINEERING JUDGMENT                             │
│                   (Design Reviewer)                              │
│   Decides: PASS / FAIL / INSUFFICIENT_EVIDENCE                   │
│   Uses extracted evidence items ONLY — never gold labels         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   VERIFICATION                                   │
│   Decides: APPROVE │ RETRY_EVIDENCE │ ABSTAIN                    │
│   Blocks PASS without evidence_id citations                      │
│   Routes workflow back to extraction when evidence incomplete    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   EVIDENCE-GATED REPORT                          │
│   design_review.md — every verdict traceable to evidence         │
└─────────────────────────────────────────────────────────────────┘
```

## Baseline (for comparison)

```
measurements.json  →  single script  →  PASS / FAIL  (no verifier, no retry)
```

## Strongest demo routing example

**C09 — multi-resonance S11**

```
Phase 1: JSON only        → Verifier: RETRY_EVIDENCE (invoke S11 tools)
Phase 2: + S11 analysis   → Design Reviewer: FAIL (dual resonance)
                          → Verifier: APPROVE
```
