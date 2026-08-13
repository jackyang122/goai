"""ID format + core config constants (iron rules)."""

from __future__ import annotations

import re

from plos.core.config import settings
from plos.core.ids import new_id

# ULID is 26 chars of Crockford base32 (python-ulid emits lowercase here).
ULID_RE = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$", re.IGNORECASE)


def test_new_id_format_is_type_ulid():
    mid = new_id("msg")
    assert mid.startswith("msg_")
    assert ULID_RE.match(mid.split("_", 1)[1])


def test_new_ids_are_unique():
    ids = {new_id("x") for _ in range(2000)}
    assert len(ids) == 2000  # ULID monotonic-ish but collision-free at this scale


def test_new_id_preserves_prefix():
    for prefix in ("kb", "mem", "goal", "t", "card"):
        assert new_id(prefix).startswith(f"{prefix}_")


def test_iron_rule_constants():
    """The three iron-rule values are the documented defaults."""
    assert settings.weak_threshold == 0.6      # weakPoints = level < 0.6
    assert settings.embedding_dim == 1024      # BGE-M3
    assert settings.default_learner_id == "stu_001"


def test_defaults_boot_with_no_external_services():
    """With no env, every provider seam is stub/dev — app must boot dependency-free."""
    assert settings.llm_engine == "stub"
    assert settings.embedding_engine == "stub"
    assert settings.rag_engine == "stub"
    assert settings.memory_engine == "stub"
    assert settings.auth_engine == "dev"
    assert settings.auth_strict is False  # PocketBase not configured
