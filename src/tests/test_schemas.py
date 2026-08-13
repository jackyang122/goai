"""Schema contract tests — the Pydantic schemas must mirror web/lib/api/types.ts
byte-for-byte (camelCase wire JSON), including the ChatMessage.payload discriminated
union that drives the 8 conversation scenarios.
"""

from __future__ import annotations

import json

import pytest
from pydantic import TypeAdapter, ValidationError

from plos.core.time import now_iso
from plos.schemas.chat import ChatMessage, ChatPayload

PAYLOAD_ADAPTER = TypeAdapter(ChatPayload)

# ── ChatMessage.payload discriminated union (5 kinds) ─────────────────────────
VALID_PAYLOADS = [
    {"kind": "plan", "tasks": [{"id": "t1", "title": "x", "estMinutes": 5}], "rationale": "r"},
    {"kind": "coach", "steps": [{"step": "a", "detail": "b"}]},
    {"kind": "quiz", "question": {"id": "q", "type": "choice", "prompt": "p", "answer": "a", "topic": "t"}},
    {"kind": "diagnosis", "diagnosis": {"cause": "c", "evidence": "e", "remedy": "r"}},
    {"kind": "summary", "patterns": [{"type": "符号错误", "count": 3}], "suggestion": "s"},
]


@pytest.mark.parametrize("raw", VALID_PAYLOADS)
def test_payload_validates_each_kind(raw):
    obj = PAYLOAD_ADAPTER.validate_python(raw)
    assert obj.kind == raw["kind"]


def test_payload_rejects_unknown_kind():
    with pytest.raises(ValidationError):
        PAYLOAD_ADAPTER.validate_python({"kind": "nope"})


def test_payload_rejects_missing_required_field():
    # diagnosis requires its nested object; quiz requires a question.
    with pytest.raises(ValidationError):
        PAYLOAD_ADAPTER.validate_python({"kind": "diagnosis"})
    with pytest.raises(ValidationError):
        PAYLOAD_ADAPTER.validate_python({"kind": "quiz"})


def test_chatmessage_serializes_camelcase():
    """Iron rule: wire JSON is camelCase, matching types.ts field names."""
    msg = ChatMessage(
        id="m1",
        role="assistant",
        content="hi",
        createdAt=now_iso(),
        skill="learning-plan",
        status="complete",
        payload={"kind": "plan", "tasks": [], "rationale": "r"},
    )
    wire = json.loads(msg.model_dump_json())
    # camelCase field names present (not snake_case).
    assert "createdAt" in wire and "created_at" not in wire
    assert wire["payload"]["kind"] == "plan"
    assert wire["role"] == "assistant"
    assert wire["skill"] == "learning-plan"


def test_chatmessage_payload_optional():
    """Plain-text messages omit payload entirely (no payload key issues)."""
    msg = ChatMessage(id="m2", role="user", content="hi", createdAt=now_iso())
    wire = json.loads(msg.model_dump_json())
    assert "payload" not in wire or wire["payload"] is None


def test_plan_task_ref_discriminated():
    """PlanTask.type is the literal union learn|practice|review."""
    from plos.schemas.learner import PlanTask

    PlanTask(id="t", title="x", estMinutes=5, type="review")  # ok
    with pytest.raises(ValidationError):
        PlanTask(id="t", title="x", estMinutes=5, type="bogus")
