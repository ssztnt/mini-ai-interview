"""System prompts (Markdown files in this folder) and the user-message builders.

Each pipeline stage has its own prompt with one job, mirroring Anthropic
Interviewer's planning → interviewing → analysis split:

- ``planner.md``     – topic → interview plan
- ``interviewer.md`` – plan + transcript → next adaptive question
- ``analyst.md``     – plan + transcript → structured summary

User messages wrap each piece of context in XML-style tags so the model can
tell instructions apart from user-provided data.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel

from app.models import Interview, Objective

PROMPTS_DIR = Path(__file__).parent


@lru_cache
def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8").strip()


def tag(name: str, content: str) -> str:
    return f"<{name}>\n{content.strip()}\n</{name}>"


def format_plan(objectives: list[Objective]) -> str:
    return "\n".join(f"{i}. {o.theme}: {o.goal}" for i, o in enumerate(objectives, start=1))


# ── Planner ───────────────────────────────────────────────────


# LLM output schemas are deliberately constraint-free: strict JSON-schema mode
# supports only a subset of JSON Schema, and not every OpenAI-compatible provider
# supports the same subset. Business rules are enforced after parsing instead.


class PlannedObjective(BaseModel):
    theme: str
    goal: str


class PlannerOutput(BaseModel):
    research_goal: str
    objectives: list[PlannedObjective]


def planner_message(topic: str, num_objectives: int) -> str:
    return "\n\n".join(
        [
            tag("topic", topic),
            tag("objective_count", str(num_objectives)),
            f"Create the interview plan with exactly {num_objectives} objectives.",
        ]
    )


# ── Interviewer ───────────────────────────────────────────────


class InterviewerOutput(BaseModel):
    lead_in: str
    question: str


def format_transcript(interview: Interview) -> str:
    if not interview.turns:
        return "(no questions asked yet)"
    blocks = []
    for n, turn in enumerate(interview.turns, start=1):
        theme = interview.plan[turn.objective_index].theme
        blocks.append(
            f"Q{n} [objective {turn.objective_index + 1}: {theme}]: {turn.question}\n"
            f"A{n}: {turn.answer or '(not answered yet)'}"
        )
    return "\n\n".join(blocks)


def interviewer_message(interview: Interview, objective_index: int) -> str:
    objective = interview.plan[objective_index]
    number, total = objective_index + 1, len(interview.plan)
    remaining = total - number
    position = "first" if number == 1 else "final" if remaining == 0 else "middle"
    return "\n\n".join(
        [
            tag("topic", interview.topic),
            tag("research_goal", interview.research_goal),
            tag("plan", format_plan(interview.plan)),
            tag("transcript", format_transcript(interview)),
            tag("current_objective", f"{number}. {objective.theme}: {objective.goal}"),
            tag("progress", f"Question {number} of {total} ({position}; {remaining} remaining)"),
            "Write the lead-in and the next question.",
        ]
    )


# ── Analyst ───────────────────────────────────────────────────


def analyst_message(interview: Interview) -> str:
    return "\n\n".join(
        [
            tag("topic", interview.topic),
            tag("research_goal", interview.research_goal),
            tag("plan", format_plan(interview.plan)),
            tag("transcript", format_transcript(interview)),
            f"Summarise this interview. Return exactly {len(interview.plan)} findings.",
        ]
    )
