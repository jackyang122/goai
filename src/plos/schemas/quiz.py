"""Quiz / error-book schemas (types.ts: Question, QuizResult, ErrorBookItem).

``QuizResult`` gains optional ``score`` / ``rationale`` from the design doc's contract
extension — produced by the semantic grader for partial-credit and open-ended questions.
"""

from __future__ import annotations

from typing import List, Optional

from .common import CamelModel, QuestionType, SkillId


class Question(CamelModel):
    id: str
    type: QuestionType
    prompt: str
    options: Optional[List[str]] = None
    answer: str
    explanation: str = ""
    topic: str
    skill: Optional[SkillId] = None


class QuizResult(CamelModel):
    questionId: str
    correct: bool
    userAnswer: str
    topic: str
    # 〔协议扩展〕
    score: Optional[float] = None  # 0..1 partial credit
    rationale: Optional[str] = None  # why correct/wrong (grader reasoning)


class ErrorBookItem(CamelModel):
    id: str
    question: Question
    userAnswer: str
    errorType: str = "待诊断"
    ts: str
    reviewed: bool = False


class GenerateQuizRequest(CamelModel):
    learnerId: str
    topic: str
    count: int = 3


class GradeRequest(CamelModel):
    learnerId: str
    question: Question
    userAnswer: str
