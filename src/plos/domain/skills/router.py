"""SkillRouter — registry of the six skills + dispatch."""

from __future__ import annotations

from typing import Dict, List, Optional

from ...app.errors import bad_request
from ...schemas.common import SkillId
from ...schemas.skill import SkillMeta, SkillResult
from .base import Skill, SkillContext
from .coach import HomeworkCoachSkill
from .diagnosis import ErrorDiagnosisSkill
from .explain import PersonalExplainSkill
from .plan import LearningPlanSkill
from .practice import AdaptivePracticeSkill
from .summary import MistakeSummarySkill


class SkillRouter:
    def __init__(self) -> None:
        self._skills: Dict[str, Skill] = {
            "learning-plan": LearningPlanSkill(),
            "homework-coach": HomeworkCoachSkill(),
            "error-diagnosis": ErrorDiagnosisSkill(),
            "personal-explain": PersonalExplainSkill(),
            "adaptive-practice": AdaptivePracticeSkill(),
            "mistake-summary": MistakeSummarySkill(),
        }

    def list_meta(self) -> List[SkillMeta]:
        return [s.meta for s in self._skills.values()]

    def get(self, skill_id: str) -> Optional[Skill]:
        return self._skills.get(skill_id)

    async def invoke(self, ctx: SkillContext) -> SkillResult:
        skill = self._skills.get(ctx.skill_id)
        if skill is None:
            raise bad_request(f"unknown skill: {ctx.skill_id}")
        return await skill.run(ctx)
