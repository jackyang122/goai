"""error-diagnosis skill — diagnose a wrong answer (cause / evidence / remedy).

Diagnosis is *evidence*: callers that want mastery updated route it through the
MasteryEngine (quiz grade, chat diagnosis turn). This skill itself returns the structured
diagnosis and a declarative delta for the UI; it does not write mastery.
"""

from __future__ import annotations

from ...providers.llm import LLMProvider
from ...schemas.skill import Citation
from ...schemas.skill import SkillMeta, SkillResult
from .base import Skill, SkillContext
from .routing import canned_reply

META = SkillMeta(
    id="error-diagnosis",
    name="错因诊断",
    description="诊断错题根因并生成针对性讲解，写入薄弱点。",
    reads=["mastery"],
    writes=["weakPoints", "mastery"],
)


class ErrorDiagnosisSkill(Skill):
    meta = META

    async def run(self, ctx: SkillContext) -> SkillResult:
        question = ctx.input.get("question")
        user_answer = str(ctx.input.get("userAnswer", ""))
        cause, evidence, remedy = await _diagnose(ctx.providers.llm, question, user_answer)
        return SkillResult(
            skill="error-diagnosis",
            output={"cause": cause, "evidence": evidence, "remedy": remedy},
            sideEffects={},
            citations=[Citation(id="c_err", source="Memory L1", snippet=evidence)],
        )


async def _diagnose(llm: LLMProvider, question, user_answer: str):
    prompt_q = question.get("prompt") if isinstance(question, dict) else str(question)
    correct = question.get("answer") if isinstance(question, dict) else None
    if llm.is_stub:
        return (
            "符号方向错误：将 -b/2a 误写为 b/2a",
            "符号错误 3 次，集中在 -b/2a",
            "强化公式中负号属于公式本身的记忆",
        )
    msgs = [
        {
            "role": "user",
            "content": (
                f"学生答错。题目：{prompt_q}\n学生答案：{user_answer}\n正确答案：{correct}\n"
                "用 JSON 输出 {{\"cause\":..., \"evidence\":..., \"remedy\":...}}，分析错因并给补救方案。"
            ),
        }
    ]
    data = await llm.json_complete(msgs, system="你是学习诊断专家，用中文，输出严格 JSON。")
    return (
        data.get("cause", "未确定错因"),
        data.get("evidence", ""),
        data.get("remedy", "建议针对性练习巩固"),
    )
