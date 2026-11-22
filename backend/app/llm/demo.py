"""Demo-mode LLM: canned but context-aware responses, no API key needed.

It implements the same `LLMClient` interface as the real client, so the rest of
the app cannot tell the difference. It reads the tagged user message to stay
roughly on topic.
"""

import re
from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel

from app.models import Emotion, Finding, Sentiment, Summary, Theme
from app.prompts import InterviewerOutput, PlannedObjective, PlannerOutput

T = TypeVar("T", bound=BaseModel)

_DEMO_OBJECTIVES = [
    ("Current experience", "Understand how {topic} shows up in the participant's day-to-day life."),
    ("Getting started", "Learn how the participant first came into contact with {topic}."),
    ("Challenges", "Explore the main frustrations or obstacles they face with {topic}."),
    ("Impact and value", "Understand what has changed for them because of {topic}."),
    ("Looking ahead", "Learn what they hope for, or worry about, as {topic} evolves."),
]


def read_tag(message: str, name: str, default: str = "") -> str:
    match = re.search(rf"<{name}>\n(.*?)\n</{name}>", message, re.DOTALL)
    return match.group(1).strip() if match else default


class DemoClient:
    def __init__(self) -> None:
        self._responders: dict[type[BaseModel], Callable[[str], Any]] = {
            PlannerOutput: self._plan,
            InterviewerOutput: self._question,
            Summary: self._summary,
        }

    def register(self, schema: type[BaseModel], responder: Callable[[str], Any]) -> None:
        self._responders[schema] = responder

    def generate(self, *, system: str, user: str, schema: type[T]) -> T:
        try:
            responder = self._responders[schema]
        except KeyError as exc:
            raise NotImplementedError(f"No demo response for {schema.__name__}") from exc
        return responder(user)

    @staticmethod
    def _plan(user: str) -> PlannerOutput:
        topic = read_tag(user, "topic", "this topic")
        count = int(read_tag(user, "objective_count", "4"))
        indices = [0, 2, 3, 4, 1][:count]  # always keep a natural arc
        return PlannerOutput(
            research_goal=f"Understand how the participant experiences {topic} in their own life.",
            objectives=[
                PlannedObjective(
                    theme=_DEMO_OBJECTIVES[i][0], goal=_DEMO_OBJECTIVES[i][1].format(topic=topic)
                )
                for i in sorted(indices)
            ],
        )

    @staticmethod
    def _question(user: str) -> InterviewerOutput:
        topic = read_tag(user, "topic", "this topic")
        objective = read_tag(user, "current_objective", "1. Experience: ")
        theme = objective.split(". ", 1)[-1].split(":", 1)[0].strip().lower()
        transcript = read_tag(user, "transcript")
        answers = re.findall(r"^A\d+: (.+)$", transcript, re.MULTILINE)

        if not answers:
            lead_in = f"Thanks for joining. Let's talk about {topic}."
        else:
            snippet = answers[-1].strip().rstrip(".")
            snippet = snippet if len(snippet) <= 60 else snippet[:57].rstrip() + "…"
            lead_in = f"Interesting. You mentioned “{snippet}”."
        return InterviewerOutput(
            lead_in=lead_in,
            question=f"Thinking about {theme}, could you share a recent, concrete example "
            f"of how that plays out for you with {topic}?",
        )

    @staticmethod
    def _summary(user: str) -> Summary:
        topic = read_tag(user, "topic", "this topic")
        transcript = read_tag(user, "transcript")
        themes = re.findall(r"^Q\d+ \[objective \d+: (.+?)\]:", transcript, re.MULTILINE)
        answers = re.findall(r"^A\d+: (.+)$", transcript, re.MULTILINE)
        return Summary(
            overview=(
                f"(Demo mode) The participant shared their experience with {topic} across "
                f"{len(answers)} questions. Add an API key to get a real AI-written summary."
            ),
            findings=[
                Finding(
                    objective=theme,
                    finding=f"The participant described their perspective on {theme.lower()}.",
                    quote=" ".join(answer.split()[:12]),
                )
                for theme, answer in zip(themes, answers, strict=False)
            ],
            themes=[
                Theme(name="Personal experience", description=f"How {topic} fits their routine."),
                Theme(name="Room to improve", description="Points where expectations fall short."),
            ],
            key_points=[
                f"Answered {len(answers)} questions about {topic}.",
                "This summary is a placeholder generated without an LLM.",
                "Set OPENAI_API_KEY or Foundry settings in .env for real analysis.",
            ],
            sentiment=Sentiment(label="neutral", score=0.0, rationale="Demo mode does not score."),
            emotions=[Emotion(name="curiosity", intensity="medium")],
            keywords=[topic.lower(), "experience", "demo"],
        )
