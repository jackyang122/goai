"""adaptive-practice skill — pick questions by weak topic + mastery (difficulty)."""

from __future__ import annotations

from typing import List

from ...db.repositories import QuestionRepository
from ...schemas.skill import Citation
from ...schemas.skill import SkillMeta, SkillResult, StepTrace
from ...seed.data import QUESTION_BANK
from .base import Skill, SkillContext

META = SkillMeta(
    id="adaptive-practice",
    name="自适应练习",
    description="按薄弱点与掌握度生成难度自适应的题目序列。",
    reads=["mastery", "weakPoints"],
    writes=["mastery"],
)


class AdaptivePracticeSkill(Skill):
    meta = META

    async def run(self, ctx: SkillContext) -> SkillResult:
        topic = str(ctx.input.get("topic") or "") or (ctx.weak_points[0].topic if ctx.weak_points else "二次函数")
        count = int(ctx.input.get("count", 3))

        repo = QuestionRepository(ctx.session)
        rows = await repo.list_by_topic(topic, limit=count)
        if not rows:
            # Fall back to the seeded bank (DB may be empty before seeding questions).
            rows = []
        # Augment from the static seed bank if the DB didn't have enough.
        questions = [self._row_to_dict(r) for r in rows]
        if len(questions) < count:
            for q in QUESTION_BANK.get(topic, QUESTION_BANK["二次函数"])[: count - len(questions)]:
                questions.append(q)

        base_level = next((m.level for m in ctx.mastery if m.topic == topic), None)
        citation = Citation(
            id="c_practice",
            source="题库 · adaptive-practice",
            snippet=f"topic={topic}" + (f", base_level={base_level:.2f}" if base_level else ""),
        )
        return SkillResult(
            skill="adaptive-practice",
            output={"questions": questions[:count]},
            sideEffects={},
            citations=[citation],
            trace=[StepTrace(step=f"选题 topic={topic}, base_level 检索")],
        )

    @staticmethod
    def _row_to_dict(r) -> dict:
        return {
            "id": r.id,
            "type": r.type,
            "prompt": r.prompt,
            "options": r.options,
            "answer": r.answer,
            "explanation": r.explanation,
            "topic": r.topic,
            "skill": r.skill,
        }
