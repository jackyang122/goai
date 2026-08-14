"""Numeric helpers."""

from __future__ import annotations


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def clamp01(x: float) -> float:
    """Clamp to the mastery/probability range [0, 1]."""
    return clamp(x, 0.0, 1.0)


def round_mastery(x: float, ndigits: int = 2) -> float:
    """Round a mastery level for display parity with the frontend."""
    return round(clamp01(x), ndigits)
