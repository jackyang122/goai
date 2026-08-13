"""ORM models (the SQL schema). Repositories are the only callers of these.

Kept relationship-free on purpose: under async, lazy ORM relationships are a common
source of ``MissingGreenlet`` errors, so joins are performed explicitly in repositories.
"""

from __future__ import annotations

from .cards import FlashCard
from .chat import Attachment, Message, Thread
from .goals import Goal, PlanTask
from .kb import KbDocument, KnowledgeBase
from .learners import Activity, Learner
from .mastery import Mastery, MasteryParam
from .memory import Memory, MemoryEdge
from .quiz import ErrorBook, Question

__all__ = [
    "Activity",
    "Attachment",
    "ErrorBook",
    "FlashCard",
    "Goal",
    "KbDocument",
    "KnowledgeBase",
    "Learner",
    "Mastery",
    "MasteryParam",
    "Memory",
    "MemoryEdge",
    "Message",
    "PlanTask",
    "Question",
    "Thread",
]
