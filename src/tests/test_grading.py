"""SemanticGrader — choice/fill/open grading, normalization, partial credit."""

from __future__ import annotations

import pytest

from src.domain.grading import SemanticGrader
from src.providers.registry import build_providers
from src.schemas.quiz import Question

# build_providers() with no env → all stubs; grader uses deterministic paths.
PROVIDERS = build_providers()
GRADER = SemanticGrader(PROVIDERS)


def _choice(answer="(2, -1)"):
    return Question(
        id="q1", type="choice", prompt="顶点坐标？",
        options=["(2,-1)", "(2,1)"], answer=answer, explanation="e", topic="二次函数",
    )


def _fill(answer="下"):
    return Question(id="q2", type="fill", prompt="开口方向？", answer=answer, explanation="e", topic="二次函数")


def _open(answer="x=-1"):
    return Question(id="q3", type="open", prompt="求对称轴", answer=answer, explanation="e", topic="二次函数")


async def test_choice_correct_despite_formatting():
    """Normalization strips spaces/commas/parens: '(2,-1)' ≡ '(2, -1)'."""
    out = await GRADER.grade(_choice(), "(2,-1)")
    assert out.correct and out.score == 1.0


async def test_choice_wrong():
    out = await GRADER.grade(_choice(), "(2, 1)")
    assert not out.correct and out.score == 0.0


async def test_fill_correct_and_wrong():
    assert (await GRADER.grade(_fill(), "下")).correct
    wrong = await GRADER.grade(_fill(), "上")
    assert not wrong.correct and wrong.score == 0.0
    # Stub path attaches the explanation as rationale.
    assert wrong.rationale == "e"


async def test_open_partial_credit_when_wrong_with_stub():
    """Open-ended wrong answers get partial credit (0.5) under the stub, not a hard 0."""
    right = await GRADER.grade(_open(), "x=-1")
    wrong = await GRADER.grade(_open(), "x=1")
    assert right.correct and right.score == 1.0
    assert not wrong.correct and wrong.score == pytest.approx(0.5)
