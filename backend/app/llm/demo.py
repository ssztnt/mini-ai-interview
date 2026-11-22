"""Demo-mode LLM: canned but context-aware responses, no API key needed.

It implements the same `LLMClient` interface as the real client, so the rest of
the app cannot tell the difference. It reads the tagged user message to stay
roughly on topic.
"""

import re
from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel

from app.prompts import PlannedObjective, PlannerOutput

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
