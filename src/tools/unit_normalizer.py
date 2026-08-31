"""Deterministic unit normalization for RF metrics."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ParsedQuantity:
    value: float
    unit: str
    canonical_unit: str
    canonical_value: float


FREQ_TO_GHZ = {
    "hz": 1e-9,
    "khz": 1e-6,
    "mhz": 1e-3,
    "ghz": 1.0,
}

BANDWIDTH_TO_MHZ = {
    "hz": 1e-6,
    "khz": 1e-3,
    "mhz": 1.0,
    "ghz": 1e3,
}


def _parse_number(text: str) -> float:
    text = text.strip().replace(",", "")
    return float(text)


def parse_frequency(value: str | float | int, unit: str | None = None) -> ParsedQuantity:
    """Parse frequency to canonical GHz."""
    if isinstance(value, (int, float)):
        u = (unit or "GHz").lower()
        factor = FREQ_TO_GHZ.get(u.replace(" ", ""), 1.0)
        canonical = float(value) * factor
        return ParsedQuantity(float(value), unit or "GHz", "GHz", canonical)

    text = str(value).strip()
    match = re.match(
        r"^([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*(Hz|kHz|MHz|GHz|hz|khz|mhz|ghz)?$",
        text,
    )
    if not match:
        raise ValueError(f"Cannot parse frequency: {value!r}")
    num = _parse_number(match.group(1))
    u = (match.group(2) or unit or "GHz").lower()
    factor = FREQ_TO_GHZ.get(u, 1.0)
    return ParsedQuantity(num, match.group(2) or unit or "GHz", "GHz", num * factor)


def parse_bandwidth(value: str | float | int, unit: str | None = None) -> ParsedQuantity:
    """Parse bandwidth to canonical MHz."""
    if isinstance(value, (int, float)):
        u = (unit or "MHz").lower()
        factor = BANDWIDTH_TO_MHZ.get(u.replace(" ", ""), 1.0)
        canonical = float(value) * factor
        return ParsedQuantity(float(value), unit or "MHz", "MHz", canonical)

    text = str(value).strip()
    match = re.match(
        r"^([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*(Hz|kHz|MHz|GHz|hz|khz|mhz|ghz)?$",
        text,
    )
    if not match:
        raise ValueError(f"Cannot parse bandwidth: {value!r}")
    num = _parse_number(match.group(1))
    u = (match.group(2) or unit or "MHz").lower()
    factor = BANDWIDTH_TO_MHZ.get(u, 1.0)
    return ParsedQuantity(num, match.group(2) or unit or "MHz", "MHz", num * factor)


def parse_gain_db(value: str | float | int) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().lower().replace("dbi", "").replace("db", "").strip()
    return _parse_number(text)


def parse_s11_db(value: str | float | int) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().lower().replace("db", "").strip()
    return _parse_number(text)


def parse_efficiency_percent(value: str | float | int) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().lower().replace("%", "").strip()
    return _parse_number(text)


def frequencies_conflict(a_ghz: float, b_ghz: float, rtol: float = 0.001) -> bool:
    if a_ghz <= 0 or b_ghz <= 0:
        return True
    return abs(a_ghz - b_ghz) / max(abs(a_ghz), abs(b_ghz)) > rtol
