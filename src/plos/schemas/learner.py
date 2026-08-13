"""Learner State schemas (types.ts: MasteryPoint … LearnerState, LearnerStateDelta)."""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import Field

from .common import CamelModel, PersonaId, Trend


class MasteryPoint(CamelModel):
    id: str
    topic: str
    subject: str
    level: float
    trend: Trend = "flat"
    lastPracticedAt: Optional[str] = None
    errorCount: int = 0


class PlanTaskRef(CamelModel):
    kind: Literal["book", "quiz", "cards"]
    id: str


class PlanTask(CamelModel):
    id: str
    title: str
    estMinutes: int = 0
    type: Literal["learn", "practice", "review"] = "learn"
    done: bool = False
    ref: Optional[PlanTaskRef] = None


class Goal(CamelModel):
    id: str
    title: str
    subject: str = ""
    progress: float = 0.0
    deadline: Optional[str] = None
    source: str = "learning-plan"
    tasks: List[PlanTask] = Field(default_factory=list)


class FlashCard(CamelModel):
    id: str
    front: str
    back: str
    topic: str
    due: str


class Activity(CamelModel):
    id: str
    type: Literal["learn", "practice", "review", "chat"]
    label: str
    ts: str


class LearnerPreferences(CamelModel):
    persona: PersonaId = "teacher"
    difficulty: Literal["adaptive", "easy", "normal", "hard"] = "adaptive"
    dailyGoalMin: int = 45
    language: str = "zh-CN"


class LearnerState(CamelModel):
    learnerId: str
    name: str
    streak: int = 0
    studyTimeTodayMin: int = 0
    studyTimeTotalMin: int = 0
    overallMastery: float = 0.0
    weeklyChange: float = 0.0
    sessionCount: int = 0
    weeklyQuestionCount: int = 0
    goals: List[Goal] = Field(default_factory=list)
    mastery: List[MasteryPoint] = Field(default_factory=list)
    weakPoints: List[MasteryPoint] = Field(default_factory=list)
    dueCards: List[FlashCard] = Field(default_factory=list)
    recentActivity: List[Activity] = Field(default_factory=list)
    preferences: LearnerPreferences = Field(default_factory=LearnerPreferences)
    updatedAt: str = ""


class LearnerStateDelta(CamelModel):
    """Declarative patch over LearnerState produced by a skill. All fields optional."""

    mastery: Optional[List[MasteryPoint]] = None
    weakPoints: Optional[List[MasteryPoint]] = None
    goals: Optional[List[Goal]] = None
    dueCards: Optional[List[FlashCard]] = None
    recentActivity: Optional[List[Activity]] = None
    studyTimeTodayMin: Optional[int] = None


class UpdatePreferencesRequest(CamelModel):
    persona: Optional[PersonaId] = None
    difficulty: Optional[Literal["adaptive", "easy", "normal", "hard"]] = None
    dailyGoalMin: Optional[int] = None
    language: Optional[str] = None
