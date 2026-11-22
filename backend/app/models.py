"""Domain and API models.

`Interview` is the single source of truth for a session: it is what lives in
memory while the interview runs and what gets written to disk when it ends.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field

MIN_QUESTIONS = 3
MAX_QUESTIONS = 5


def utc_now() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return uuid4().hex[:12]


# ── Domain ────────────────────────────────────────────────────


class Status(StrEnum):
    PLANNING = "planning"  # plan generated, user may still edit it
    IN_PROGRESS = "in_progress"  # questions are being asked
    COMPLETED = "completed"  # summary produced and saved


class Objective(BaseModel):
    """One slot of the interview plan: what to talk about and why."""

    theme: str = Field(min_length=1, max_length=80)
    goal: str = Field(min_length=1, max_length=300)


class Turn(BaseModel):
    """One question/answer exchange, tied to the plan objective it serves."""

    objective_index: int
    lead_in: str = ""
    question: str
    answer: str | None = None
    asked_at: datetime = Field(default_factory=utc_now)
    answered_at: datetime | None = None


SentimentLabel = Literal["positive", "neutral", "negative", "mixed"]


class Finding(BaseModel):
    """What we learned for one plan objective, backed by the participant's words."""

    objective: str
    finding: str
    quote: str


class Theme(BaseModel):
    name: str
    description: str


class Emotion(BaseModel):
    name: str
    intensity: Literal["low", "medium", "high"]


class Sentiment(BaseModel):
    label: SentimentLabel
    score: float  # -1 (very negative) … +1 (very positive)
    rationale: str


class Summary(BaseModel):
    """The analyst's structured summary (also the LLM output schema)."""

    overview: str
    findings: list[Finding]
    themes: list[Theme]
    key_points: list[str]
    sentiment: Sentiment
    emotions: list[Emotion]
    keywords: list[str]


class ClassicAnalysis(BaseModel):
    """Deterministic, non-LLM baseline: VADER sentiment + YAKE keywords."""

    method: str = "VADER + YAKE"
    sentiment_label: SentimentLabel
    sentiment_score: float  # mean VADER compound score, -1 … +1
    answer_scores: list[float]  # one compound score per answer
    keywords: list[str]


class Interview(BaseModel):
    id: str = Field(default_factory=new_id)
    topic: str
    status: Status = Status.PLANNING
    provider: str
    model: str
    research_goal: str
    plan: list[Objective]
    turns: list[Turn] = []
    summary: Summary | None = None
    analysis: ClassicAnalysis | None = None
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None

    @computed_field
    @property
    def awaiting_summary(self) -> bool:
        """All plan questions are answered; the next step is the summary."""
        return (
            self.status == Status.IN_PROGRESS
            and len(self.turns) == len(self.plan)
            and self.turns[-1].answer is not None
        )

    @property
    def current_turn(self) -> Turn | None:
        """The question currently waiting for an answer, if any."""
        if self.turns and self.turns[-1].answer is None:
            return self.turns[-1]
        return None


# ── API requests ──────────────────────────────────────────────


class CreateInterviewRequest(BaseModel):
    topic: str = Field(min_length=2, max_length=120)
    num_questions: int = Field(default=4, ge=MIN_QUESTIONS, le=MAX_QUESTIONS)


class UpdatePlanRequest(BaseModel):
    objectives: list[Objective] = Field(min_length=MIN_QUESTIONS, max_length=MAX_QUESTIONS)


class AnswerRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=4000)


class InterviewListItem(BaseModel):
    """Compact row for the history view."""

    id: str
    topic: str
    completed_at: datetime | None
    num_questions: int
    sentiment: SentimentLabel | None
    overview: str | None

    @classmethod
    def from_interview(cls, interview: Interview) -> "InterviewListItem":
        return cls(
            id=interview.id,
            topic=interview.topic,
            completed_at=interview.completed_at,
            num_questions=len(interview.plan),
            sentiment=interview.summary.sentiment.label if interview.summary else None,
            overview=interview.summary.overview if interview.summary else None,
        )
