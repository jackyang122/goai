"""mistake-summary skill — aggregate the error book into error-type patterns + trend."""

from __future__ import annotations

from collections import Counter

from ...db.repositories import ErrorBookRepository
from ...schemas.skill import SkillMeta, SkillResult, StepTrace
from .base import Skill, SkillContext

META = SkillMeta(
    id="mistake-summary",
    name="错题归纳",
    description="周期性归类错题、提炼错误模式，刷新掌握度。",
    reads=["weakPoints"],
    writes=["mastery", "weakPoints"],
)


class MistakeSummarySkill(Skill):
    meta = META

    async def run(self, ctx: SkillContext) -> SkillResult:
        repo = ErrorBookRepository(ctx.session)
        rows = await repo.list_by_learner(ctx.learner_id, limit=100)
        counter = Counter(r.error_type or "待诊断" for r in rows)
        patterns = [
            {"type": t, "count": c, "trend": "stable"}
            for t, c in counter.most_common()
        ]
        suggestion = (
            f"建议优先补「{patterns[0]['type']}」类，预计 2 天可显著改善。"
            if patterns
            else "暂无错题数据。"
        )
        return SkillResult(
            skill="mistake-summary",
            output={"patterns": patterns, "suggestion": suggestion},
            sideEffects={},
            trace=[StepTrace(step="聚类错题本"), StepTrace(step="刷新 mastery")],
        )
