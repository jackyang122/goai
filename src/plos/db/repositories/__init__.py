"""Repository layer — the ONLY place that emits SQL.

Importing these by aggregate keeps the namespace tidy. ``MasteryRepository`` exposes
read methods publicly; its single write path ``commit_update`` is called exclusively by
:class:`MasteryEngine <plos.domain.mastery.MasteryEngine>` (enforced by CI grep + name
convention) — this is the single-writer rule for ``mastery``/``weakPoints``.
"""

from __future__ import annotations

from .base import BaseRepository
from .cards import CardRepository
from .chat import AttachmentRepository, MessageRepository, ThreadRepository
from .goals import GoalRepository, PlanTaskRepository
from .kb import KbDocumentRepository, KbRepository
from .learner import ActivityRepository, LearnerRepository
from .mastery import MasteryParamRepository, MasteryRepository
from .memory import MemoryEdgeRepository, MemoryRepository
from .quiz import ErrorBookRepository, QuestionRepository

__all__ = [
    "ActivityRepository",
    "AttachmentRepository",
    "BaseRepository",
    "CardRepository",
    "ErrorBookRepository",
    "GoalRepository",
    "KbDocumentRepository",
    "KbRepository",
    "LearnerRepository",
    "MasteryParamRepository",
    "MasteryRepository",
    "MemoryEdgeRepository",
    "MemoryRepository",
    "MessageRepository",
    "PlanTaskRepository",
    "QuestionRepository",
    "ThreadRepository",
]
