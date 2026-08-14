"""Skill router meta + keyword routing.

pick_skill is a faithful mirror of web/lib/api/mock.ts:pickSkill — same keyword
sets, same precedence. These tests pin the canonical keyword→skill mapping so a
regression (or divergence from the frontend mock) is caught immediately.
"""

from __future__ import annotations

import pytest

from src.domain.skills.router import SkillRouter
from src.domain.skills.routing import canned_reply, pick_skill

SIX_SKILLS = {
    "learning-plan",
    "homework-coach",
    "error-diagnosis",
    "personal-explain",
    "adaptive-practice",
    "mistake-summary",
}


def test_router_lists_all_six_skills():
    metas = SkillRouter().list_meta()
    ids = {m.id for m in metas}
    assert ids == SIX_SKILLS


def test_every_meta_declares_reads_and_writes():
    """SkillMeta carries the data-flow contract (what it reads / writes)."""
    for m in SkillRouter().list_meta():
        assert isinstance(m.reads, list)
        assert isinstance(m.writes, list)


@pytest.mark.parametrize(
    "text,expected",
    [
        ("帮我做个学习计划", "learning-plan"),
        ("今天该怎么学", "learning-plan"),
        ("做几道练习题", "adaptive-practice"),
        ("帮我刷题", "adaptive-practice"),
        ("这题错在哪", "error-diagnosis"),
        ("错因是什么", "error-diagnosis"),
        ("归纳本周错误", "mistake-summary"),
        ("这道作业", "homework-coach"),
        ("这题怎么做", "homework-coach"),
        ("解释一下概念", "personal-explain"),  # no keyword → default
    ],
)
def test_pick_skill_canonical_keywords(text, expected):
    assert pick_skill(text) == expected


def test_canned_reply_nonempty_for_every_skill():
    for skill in SIX_SKILLS:
        # Route a canonical keyword for each, then ensure the canned reply exists.
        text = {
            "learning-plan": "学习计划",
            "adaptive-practice": "练习题",
            "error-diagnosis": "错在哪",
            "mistake-summary": "归纳错误",
            "homework-coach": "这道作业",
            "personal-explain": "解释概念",
        }[skill]
        assert pick_skill(text) == skill
        reply = canned_reply(text)
        assert isinstance(reply, str) and reply.strip()
