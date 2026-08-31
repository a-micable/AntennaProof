"""Deterministic S11 CSV analysis."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO
from pathlib import Path


@dataclass
class S11Analysis:
    resonant_frequency_ghz: float | None
    minimum_s11_db: float | None
    bandwidth_mhz: float | None
    resonance_count: int
    notes: list[str]


def _read_rows(path: Path) -> list[tuple[float, float]]:
    text = path.read_text(encoding="utf-8")
    reader = csv.DictReader(StringIO(text))
    rows: list[tuple[float, float]] = []
    for row in reader:
        freq_key = next((k for k in row if "freq" in k.lower()), None)
        s11_key = next((k for k in row if "s11" in k.lower()), None)
        if not freq_key or not s11_key:
            continue
        rows.append((float(row[freq_key]), float(row[s11_key])))
    if not rows:
        raise ValueError(f"No valid rows in {path}")
    return rows


def analyze_s11_csv(path: Path, threshold_db: float = -10.0) -> S11Analysis:
    rows = _read_rows(path)
    notes: list[str] = []

    min_s11 = min(s11 for _, s11 in rows)
    min_idx = next(i for i, (_, s11) in enumerate(rows) if s11 == min_s11)
    resonant_freq = rows[min_idx][0]

    resonance_indices: list[int] = []
    for i in range(1, len(rows) - 1):
        _, s_prev = rows[i - 1]
        _, s_cur = rows[i]
        _, s_next = rows[i + 1]
        if s_cur <= s_prev and s_cur <= s_next and s_cur <= -7.0:
            resonance_indices.append(i)

    resonance_count = max(1, len(resonance_indices))
    if len(resonance_indices) > 1:
        notes.append(f"Multiple resonances detected ({len(resonance_indices)})")

    below = [(f, s) for f, s in rows if s <= threshold_db]
    bandwidth_mhz = None
    if below:
        freqs = [f for f, _ in below]
        bandwidth_mhz = (max(freqs) - min(freqs)) * 1000

    return S11Analysis(
        resonant_frequency_ghz=resonant_freq,
        minimum_s11_db=min_s11,
        bandwidth_mhz=bandwidth_mhz,
        resonance_count=resonance_count,
        notes=notes,
    )
