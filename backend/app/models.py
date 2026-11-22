"""Domain and API models.

`Interview` is the single source of truth for a session: it is what lives in
memory while the interview runs and what gets written to disk when it ends.
"""

from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field

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


class Interview(BaseModel):
    id: str = Field(default_factory=new_id)
    topic: str
    status: Status = Status.PLANNING
    provider: str
    model: str
    research_goal: str
    plan: list[Objective]
    turns: list[Turn] = []
    created_at: datetime = Field(default_factory=utc_now)
    completed_at: datetime | None = None

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
