"""learning-plan skill — generate a daily study track from mastery + weak points."""

from __future__ import annotations

from typing import List

from ...schemas.skill import Citation
from ...schemas.learner import LearnerStateDelta, PlanTask
from ...schemas.skill import SkillMeta, SkillResult, StepTrace
from .base import Skill, SkillContext

META = SkillMeta(
    id="learning-plan",
    name="学习规划",
    description="根据目标、可用时间与当前掌握度生成每日学习轨道。",
    reads=["mastery", "goals", "preferences"],
    writes=["goals"],
)


class LearningPlanSkill(Skill):
    meta = META

    async def run(self, ctx: SkillContext) -> SkillResult:
        mastery = ctx.mastery
        weak = ctx.weak_points
        available = int(ctx.input.get("availableMin", 55))

        tasks: List[PlanTask] = []
        if ctx.learner_state and ctx.learner_state.goals:
            # Re-surface the learner's existing goal tasks, prioritizing weak topics.
            for goal in ctx.learner_state.goals:
                tasks.extend(goal.tasks)
        if not tasks:
            from ...core.ids import new_id

            # Synthesize from the two weakest topics + a review.
            focus = [w.topic for w in weak[:2]] or [m.topic for m in mastery[:2]] or ["二次函数"]
            for i, topic in enumerate(focus):
                tasks.append(
                    PlanTask(
                        id=new_id("t"),
                        title=f"{topic} · 精通路径",
                        estMinutes=min(20, available // max(1, len(focus))),
                        type="learn",
                    )
                )
            tasks.append(PlanTask(id=new_id("t"), title="错题重练 · 3 道薄弱", estMinutes=15, type="review"))

        # Trim to fit available time.
        budget, kept = available, []
        for t in tasks:
            if budget >= t.estMinutes or not kept:
                kept.append(t)
                budget -= t.estMinutes

        citation = Citation(
            id="c_plan",
            source="LearnerState · mastery[]",
            snippet=" · ".join(f"{m.topic} {m.level:.2f}" for m in (mastery[:3] or [])) or "no mastery data",
        )
        return SkillResult(
            skill="learning-plan",
            output={"plan": [t.model_dump() for t in kept], "rationale": "基于当前掌握度与薄弱点生成"},
            sideEffects=LearnerStateDelta(goals=[]),
            citations=[citation],
            trace=[StepTrace(step="读取 mastery/goals"), StepTrace(step="生成每日轨道")],
        )
