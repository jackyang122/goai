"""Skill base class + invocation context."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

from ...providers.registry import ProviderContainer
from ...schemas.common import SkillId
from ...schemas.learner import LearnerState, MasteryPoint
from ...schemas.skill import SkillMeta, SkillResult


@dataclass
class SkillContext:
    session: object  # AsyncSession
    learner_id: str
    skill_id: SkillId
    input: dict
    providers: ProviderContainer
    learner_state: Optional[LearnerState] = None

    @property
    def mastery(self) -> List[MasteryPoint]:
        return self.learner_state.mastery if self.learner_state else []

    @property
    def weak_points(self) -> List[MasteryPoint]:
        return self.learner_state.weakPoints if self.learner_state else []


class Skill(ABC):
    meta: SkillMeta

    @abstractmethod
    async def run(self, ctx: SkillContext) -> SkillResult:
        ...
