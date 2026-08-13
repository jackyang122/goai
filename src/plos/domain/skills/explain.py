"""personal-explain skill — layered explanation of a concept (KaTeX passthrough)."""

from __future__ import annotations

from ...core.ids import new_id
from ...core.time import now_iso
from ...schemas.skill import Citation
from ...schemas.learner import Activity, LearnerStateDelta
from ...schemas.skill import SkillMeta, SkillResult
from .base import Skill, SkillContext
from .routing import canned_reply

META = SkillMeta(
    id="personal-explain",
    name="个性化讲解",
    description="依据掌握度与偏好分层、换角度讲解概念。",
    reads=["mastery", "preferences"],
    writes=["recentActivity"],
)


class PersonalExplainSkill(Skill):
    meta = META

    async def run(self, ctx: SkillContext) -> SkillResult:
        concept = str(ctx.input.get("concept", "二次函数顶点"))
        text = await _explain_text(ctx, concept)
        recent = Activity(id=new_id("act"), type="chat", label=f"个性化讲解：{concept}", ts=now_iso())
        citation = Citation(
            id="c_explain",
            source="数学核心知识库 · 二次函数.pdf p.4",
            snippet="顶点 (-b/2a, (4ac-b²)/4a)",
        )
        return SkillResult(
            skill="personal-explain",
            output={"explanation": text},
            sideEffects=LearnerStateDelta(recentActivity=[recent]),
            citations=[citation],
        )


async def _explain_text(ctx: SkillContext, concept: str) -> str:
    providers = ctx.providers
    if providers.llm.is_stub:
        return canned_reply(f"解释一下{concept}")
    msgs = [{"role": "user", "content": f"用「直观 + 严格」两个角度讲解概念：{concept}，给一个例子，公式用 LaTeX $...$。"}]
    return await providers.llm.complete(
        msgs, system="你是亲切的高中老师，用中文讲解，关键公式用 LaTeX 行内 $...$ 或块 $$...$$。"
    )
