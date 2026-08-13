"""SemanticGrader — choice/fill/open grading with partial credit + rationale.

Choice/fill are normalized-exact; open-ended (and ambiguous fill) use an LLM rubric
returning a 0..1 score. Falls back to deterministic behavior when no real LLM is set.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from ..providers.registry import ProviderContainer
from ..schemas.quiz import Question


@dataclass
class GradeOutcome:
    correct: bool
    score: float
    rationale: Optional[str] = None


def _normalize(s: str) -> str:
    return re.sub(r"[\s,，。()（）]", "", s).strip().lower()


class SemanticGrader:
    def __init__(self, providers: ProviderContainer) -> None:
        self.providers = providers

    async def grade(self, question: Question, user_answer: str) -> GradeOutcome:
        qtype = question.type
        ua = (user_answer or "").strip()
        if qtype == "choice":
            ok = _normalize(ua) == _normalize(question.answer)
            return GradeOutcome(correct=ok, score=1.0 if ok else 0.0)
        if qtype == "fill":
            if _normalize(ua) == _normalize(question.answer):
                return GradeOutcome(correct=True, score=1.0)
            # Acceptable close match without an LLM.
            if not self.providers.llm.is_stub:
                return await self._llm_grade(question, ua)
            return GradeOutcome(correct=False, score=0.0, rationale=question.explanation)
        # open
        if self.providers.llm.is_stub:
            ok = _normalize(ua) == _normalize(question.answer)
            return GradeOutcome(correct=ok, score=1.0 if ok else 0.5, rationale=question.explanation)
        return await self._llm_grade(question, ua)

    async def _llm_grade(self, question: Question, user_answer: str) -> GradeOutcome:
        msgs = [
            {
                "role": "user",
                "content": (
                    f"题目：{question.prompt}\n参考答案：{question.answer}\n学生答案：{user_answer}\n"
                    "用 JSON 输出 {\"score\": 0..1, \"correct\": bool, \"rationale\": \"简短理由\"}。"
                ),
            }
        ]
        data = await self.providers.llm.json_complete(
            msgs, system="你是严格的阅卷老师，用中文，输出严格 JSON。", max_tokens=300
        )
        score = float(data.get("score", 0.0))
        correct = bool(data.get("correct", score >= 0.6))
        return GradeOutcome(correct=correct, score=score, rationale=data.get("rationale"))
