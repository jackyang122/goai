"""homework-coach skill — Socratic step-by-step guidance (no direct answers)."""

from __future__ import annotations

from ...core.ids import new_id
from ...core.time import now_iso
from ...schemas.learner import Activity, LearnerStateDelta
from ...schemas.skill import SkillMeta, SkillResult, StepTrace
from .base import Skill, SkillContext

META = SkillMeta(
    id="homework-coach",
    name="作业辅导",
    description="对题目或材料给出分步提示，引导而非直接给答案。",
    reads=["mastery", "preferences"],
    writes=["recentActivity"],
)


class HomeworkCoachSkill(Skill):
    meta = META

    async def run(self, ctx: SkillContext) -> SkillResult:
        material = str(ctx.input.get("material") or ctx.input.get("question") or "")
        steps = await _steps(ctx, material)
        recent = Activity(id=new_id("act"), type="chat", label="作业辅导：分步提示", ts=now_iso())
        return SkillResult(
            skill="homework-coach",
            output={"steps": steps},
            sideEffects=LearnerStateDelta(recentActivity=[recent]),
        )


async def _steps(ctx: SkillContext, material: str) -> list:
    providers = ctx.providers
    base = ["识别题型", "列出已知量", "匹配公式/定理", "分步求解"]
    if providers.llm.is_stub:
        return [StepTrace(step=s) for s in base]
    msgs = [
        {
            "role": "user",
            "content": f"不要给答案，只给 3-4 步苏格拉底式引导提示（每步 step + 简短 detail）。题目：{material or '（未提供题目）'}",
        }
    ]
    raw = await providers.llm.complete(
        msgs, system="你是苏格拉底式辅导老师，用中文，只引导不给答案。", max_tokens=400
    )
    lines = [ln.lstrip("0123456789.-) ").strip() for ln in raw.splitlines() if ln.strip()]
    steps = [StepTrace(step=ln) for ln in lines[:4]]
    return steps or [StepTrace(step=s) for s in base]
