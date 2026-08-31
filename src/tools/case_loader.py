"""Load case bundles from disk."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from src.tools.s11_analyzer import S11Analysis, analyze_s11_csv


@dataclass
class CaseBundle:
    case_id: str
    case_dir: Path
    requirements: dict
    measurements: dict = field(default_factory=dict)
    notes: str = ""
    s11_path: Path | None = None
    s11_analysis: S11Analysis | None = None
    ground_truth_path: Path | None = None


def load_case(case_dir: Path) -> CaseBundle:
    case_id = case_dir.name.split("_")[0]
    req = json.loads((case_dir / "requirements.json").read_text(encoding="utf-8"))
    case_id = req.get("case_id", case_id)

    measurements: dict = {}
    meas_path = case_dir / "measurements.json"
    if meas_path.exists():
        raw = meas_path.read_text(encoding="utf-8").strip()
        if raw and raw != "{}":
            measurements = json.loads(raw)

    notes_path = case_dir / "notes.txt"
    notes = notes_path.read_text(encoding="utf-8") if notes_path.exists() else ""

    s11_path = case_dir / "s11.csv" if (case_dir / "s11.csv").exists() else None
    s11_analysis = analyze_s11_csv(s11_path) if s11_path else None

    gt_path = case_dir / "ground_truth.json"

    return CaseBundle(
        case_id=case_id,
        case_dir=case_dir,
        requirements=req,
        measurements=measurements,
        notes=notes,
        s11_path=s11_path,
        s11_analysis=s11_analysis,
        ground_truth_path=gt_path if gt_path.exists() else None,
    )


def list_cases(data_root: Path) -> list[Path]:
    seen: set[str] = set()
    cases: list[Path] = []
    for path in sorted(data_root.iterdir()):
        if not path.is_dir() or path.name[0] not in ("C", "H"):
            continue
        cid = path.name.split("_")[0]
        if cid in seen:
            continue
        if not (path / "requirements.json").exists():
            continue
        seen.add(cid)
        cases.append(path)
    return cases
