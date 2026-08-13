"""Bayesian Knowledge Tracing — closed-form forward filter.

The online update is the standard BKT posterior-then-transit step (design doc §6.1).
``pybkt.fit()`` is reserved for *offline* re-estimation (CLI ``recompute-mastery``); the
serving path uses these pure functions only.

Verification (UC-B, params L0=0.55 T=0.10 S=0.30 G=0.30):
    wrong  -> 0.55 -> 0.41
    correct-> 0.41 -> 0.66
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ...core.units import clamp01


@dataclass(frozen=True)
class BktParams:
    l0: float = 0.5      # P(L_0)
    t: float = 0.1       # P(learn | not known) transit
    slip: float = 0.2    # P(wrong | known)
    guess: float = 0.2   # P(correct | not known)


def p_correct(level: float, p: BktParams) -> float:
    """P(observation = correct) marginal over the latent known/unknown state."""
    return level * (1.0 - p.slip) + (1.0 - level) * p.guess


def posterior(level: float, observed: bool, p: BktParams) -> float:
    """P(known | observation), the Bayesian belief update (pre-transit)."""
    pc = level * (1.0 - p.slip) + (1.0 - level) * p.guess
    pw = level * p.slip + (1.0 - level) * (1.0 - p.guess)
    if observed:
        return clamp01((level * (1.0 - p.slip)) / pc) if pc > 0 else level
    return clamp01((level * p.slip) / pw) if pw > 0 else level


def transit(level: float, p: BktParams) -> float:
    """Apply the learn-once transition: P(L_{n}) = post + (1 - post) * T."""
    return clamp01(level + (1.0 - level) * p.t)


def forward(level: float, observed: bool, p: BktParams) -> float:
    """One full BKT step: posterior then transit (the value to persist as ``level``)."""
    return transit(posterior(level, observed, p), p)


def soft_forward(level: float, observed: bool, p: BktParams, weight: float = 1.0) -> float:
    """Partial-credit update: blend the hard update with the prior by ``weight`` ∈ (0, 1].

    ``weight=1`` is a hard observation; smaller weights model soft evidence (an FSRS
    review, a diagnosis confirmation) that should nudge but not snap the belief.
    """
    w = clamp01(weight)
    hard = forward(level, observed, p)
    return clamp01(level + w * (hard - level))


def trend(prev: float, curr: float) -> Literal["up", "down", "flat"]:
    """Coarse trend label from a level delta (frontend ``Trend``)."""
    eps = 0.01
    if curr - prev > eps:
        return "up"
    if prev - curr > eps:
        return "down"
    return "flat"


# ── Self-check (run via ``python -m plos.domain.mastery.bkt``) ─────────────────
if __name__ == "__main__":  # pragma: no cover
    p = BktParams(0.55, 0.10, 0.30, 0.30)
    after_wrong = forward(0.55, False, p)
    after_right = forward(after_wrong, True, p)
    print(f"wrong  -> 0.55 -> {after_wrong:.4f}")   # ~0.4094
    print(f"correct-> {after_wrong:.4f} -> {after_right:.4f}")  # ~0.6561
