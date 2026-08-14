"""BKT closed-form forward filter — reproduces design-doc UC-B exactly."""

from __future__ import annotations

from src.domain.mastery.bkt import (
    BktParams,
    forward,
    p_correct,
    posterior,
    soft_forward,
    transit,
    trend,
)

# UC-B parameters (docs/后端逻辑设计.md): L0=0.55, T=0.10, S=0.30, G=0.30
P = BktParams(l0=0.55, t=0.10, slip=0.30, guess=0.30)


def test_uc_b_wrong_then_correct_matches_design_doc():
    """0.55 --wrong--> 0.4094 --correct--> 0.6561 (the canonical BKT self-check)."""
    after_wrong = forward(0.55, False, P)
    assert round(after_wrong, 4) == 0.4094
    after_right = forward(after_wrong, True, P)
    assert round(after_right, 4) == 0.6561


def test_level_stays_in_unit_interval():
    """Iron rule: mastery.level ∈ [0,1] — forward must never escape it."""
    for start in (0.0, 0.55, 1.0):
        for observed in (True, False):
            for params in (P, BktParams(0.1, 0.5, 0.45, 0.45)):
                assert 0.0 <= forward(start, observed, params) <= 1.0


def test_correct_observation_raises_belief():
    assert forward(0.5, True, P) > 0.5
    assert forward(0.5, False, P) < 0.5


def test_transit_adds_learning():
    # transit always moves belief upward (toward 1) by the slip/guess-bounded amount.
    assert transit(0.5, P) > 0.5
    assert transit(1.0, P) == 1.0


def test_p_correct_is_a_probability():
    for level in (0.0, 0.3, 0.7, 1.0):
        pc = p_correct(level, P)
        assert 0.0 <= pc <= 1.0
    # A known learner is (mostly) correct: p_correct rises with level.
    assert p_correct(0.9, P) > p_correct(0.1, P)


def test_posterior_is_bayesian_update():
    # Posterior after a correct observation must exceed the prior.
    assert posterior(0.5, True, P) > 0.5
    assert posterior(0.5, False, P) < 0.5


def test_soft_forward_blends_prior_and_hard_update():
    """weight=1 ≡ hard forward; weight=0 ≡ no change; monotonic in weight."""
    start = 0.5
    hard = forward(start, True, P)
    none_ = soft_forward(start, True, P, weight=0.0)
    half = soft_forward(start, True, P, weight=0.5)
    full = soft_forward(start, True, P, weight=1.0)
    assert abs(none_ - start) < 1e-9
    assert abs(full - hard) < 1e-9
    assert start < half < hard  # monotonic blend toward the hard update


def test_trend_labels():
    assert trend(0.4, 0.5) == "up"
    assert trend(0.5, 0.4) == "down"
    assert trend(0.5, 0.505) == "flat"
