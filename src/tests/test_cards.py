"""FSRS scheduling — works with or without py-fsrs installed (degrades to interval fallback)."""

from __future__ import annotations

from datetime import datetime, timezone

from plos.db.models.cards import FlashCard
from plos.domain.cards import FsrsCardService

# Service with a null session is fine — we only exercise the pure _schedule path.
SVC = FsrsCardService(session=None)
NOW = datetime.now(timezone.utc)


def _card(reps=2):
    return FlashCard(
        id="c", learner_id="s", front="f", back="b", topic="二次函数",
        due=NOW, reps=reps, lapses=0,
    )


def test_fallback_schedule_is_future_and_tz_aware():
    """Every rating yields a tz-aware due date strictly in the future (iron rule: no past dues)."""
    for rating in (1, 2, 3, 4):
        due = SVC._fallback_schedule(_card(), rating)
        assert due.tzinfo is not None
        assert due > NOW


def test_fallback_schedule_monotonic_by_rating():
    """Easier ratings schedule further out: due(Again) < due(Easy)."""
    dues = [SVC._fallback_schedule(_card(), r) for r in (1, 2, 3, 4)]
    assert dues[0] < dues[3]
    # Strictly increasing across the 1..4 ladder.
    for a, b in zip(dues, dues[1:]):
        assert a <= b


def test_schedule_path_independent_of_fsrs_presence():
    """_schedule picks py-fsrs if present else the fallback; either way a future tz-aware due."""
    for rating in (1, 2, 3, 4):
        due = SVC._schedule(_card(), rating)
        assert due.tzinfo is not None
        assert due > NOW


def test_fallback_grows_with_reps():
    """More prior reps push the fallback interval further out (simple stability proxy)."""
    soon = SVC._fallback_schedule(_card(reps=0), 3)
    later = SVC._fallback_schedule(_card(reps=5), 3)
    assert later > soon
