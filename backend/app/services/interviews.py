"""The interview lifecycle: plan → (edit) → ask/answer loop → summary.

The service owns the rules (status transitions, plan size); the LLM only
writes text. Status flow::

    planning ──start──▶ in_progress ──complete──▶ completed
"""

import re

from app.config import LLMConfig
from app.llm import LLMClient, LLMError
from app.models import (
    MAX_QUESTIONS,
    MIN_QUESTIONS,
    Interview,
    Objective,
    Status,
    Summary,
    Turn,
    utc_now,
)
from app.prompts import (
    InterviewerOutput,
    PlannerOutput,
    analyst_message,
    interviewer_message,
    load_prompt,
    planner_message,
)
from app.services.analysis import analyze_answers
from app.storage import InMemoryInterviewRepository, JsonInterviewStore


class InterviewNotFound(LookupError):
    pass


class InvalidState(RuntimeError):
    """The requested action is not allowed in the interview's current status."""


class InterviewService:
    def __init__(
        self,
        llm: LLMClient,
        llm_config: LLMConfig,
        repository: InMemoryInterviewRepository,
        store: JsonInterviewStore,
    ) -> None:
        self._llm = llm
        self._llm_config = llm_config
        self._repo = repository
        self._store = store

    # ── Lookup ────────────────────────────────────────────────

    def get(self, interview_id: str) -> Interview:
        """In-progress interviews live in memory; completed ones on disk."""
        interview = self._repo.get(interview_id) or self._store.get(interview_id)
        if interview is None:
            raise InterviewNotFound(interview_id)
        return interview

    def list_completed(self) -> list[Interview]:
        return self._store.list()

    def _require(self, interview_id: str, status: Status) -> Interview:
        interview = self.get(interview_id)
        if interview.status != status:
            raise InvalidState(f"Interview is '{interview.status}', expected '{status}'")
        return interview

    # ── Planning ──────────────────────────────────────────────

    def create(self, topic: str, num_questions: int) -> Interview:
        topic = topic.strip()
        result = self._llm.generate(
            system=load_prompt("planner"),
            user=planner_message(topic, num_questions),
            schema=PlannerOutput,
        )
        objectives = [
            Objective(theme=o.theme.strip(), goal=o.goal.strip())
            for o in result.objectives[:num_questions]
        ]
        if len(objectives) < MIN_QUESTIONS:
            raise LLMError(f"Planner returned only {len(objectives)} objectives")

        interview = Interview(
            topic=topic,
            provider="demo" if self._llm_config.demo else self._llm_config.provider,
            model="canned responses" if self._llm_config.demo else self._llm_config.model,
            research_goal=result.research_goal.strip(),
            plan=objectives,
        )
        self._repo.save(interview)
        return interview

    def update_plan(self, interview_id: str, objectives: list[Objective]) -> Interview:
        interview = self._require(interview_id, Status.PLANNING)
        if not MIN_QUESTIONS <= len(objectives) <= MAX_QUESTIONS:
            raise InvalidState(f"A plan needs {MIN_QUESTIONS}–{MAX_QUESTIONS} objectives")
        interview.plan = objectives
        self._repo.save(interview)
        return interview

    # ── Interviewing ──────────────────────────────────────────

    def start(self, interview_id: str) -> Interview:
        """Lock the plan and ask the first question."""
        interview = self._require(interview_id, Status.PLANNING)
        updated = interview.model_copy(deep=True)
        updated.status = Status.IN_PROGRESS
        self._ask_next(updated)
        self._repo.save(updated)
        return updated

    def answer(self, interview_id: str, answer: str) -> Interview:
        """Record the answer and, unless the plan is finished, ask the next question.

        Works on a copy so the stored interview only changes if everything
        succeeds: if the LLM fails, the user can simply resubmit the answer.
        """
        interview = self._require(interview_id, Status.IN_PROGRESS)
        if interview.current_turn is None:
            raise InvalidState("There is no open question to answer")

        updated = interview.model_copy(deep=True)
        turn = updated.current_turn
        turn.answer = answer.strip()
        turn.answered_at = utc_now()
        if len(updated.turns) < len(updated.plan):
            self._ask_next(updated)
        self._repo.save(updated)
        return updated

    # ── Analysis ──────────────────────────────────────────────

    def complete(self, interview_id: str) -> Interview:
        """Summarise with the LLM, add the classic baseline, and persist to disk."""
        interview = self._require(interview_id, Status.IN_PROGRESS)
        if not interview.awaiting_summary:
            raise InvalidState("All questions must be answered before summarising")

        summary = self._llm.generate(
            system=load_prompt("analyst"),
            user=analyst_message(interview),
            schema=Summary,
        )
        answers = [t.answer or "" for t in interview.turns]

        updated = interview.model_copy(deep=True)
        summary = label_findings(summary, interview.plan)
        updated.summary = keep_verbatim_quotes(summary, answers)
        updated.analysis = analyze_answers(answers)
        updated.status = Status.COMPLETED
        updated.completed_at = utc_now()

        self._store.save(updated)
        self._repo.delete(interview_id)
        return updated

    def _ask_next(self, interview: Interview) -> None:
        objective_index = len(interview.turns)
        result = self._llm.generate(
            system=load_prompt("interviewer"),
            user=interviewer_message(interview, objective_index),
            schema=InterviewerOutput,
        )
        interview.turns.append(
            Turn(
                objective_index=objective_index,
                lead_in=result.lead_in.strip(),
                question=result.question.strip(),
            )
        )


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().strip("\"'“”‘’").lower()


def keep_verbatim_quotes(summary: Summary, answers: list[str]) -> Summary:
    """Drop any quote that does not appear in the participant's answers.

    Models sometimes "tidy up" quotes; a quote attributed to the participant
    must be their actual words, so unverifiable ones are blanked.
    """
    corpus = _normalise(" ".join(answers))
    for finding in summary.findings:
        if finding.quote and _normalise(finding.quote) not in corpus:
            finding.quote = ""
    return summary


def label_findings(summary: Summary, plan: list[Objective]) -> Summary:
    """Name each finding after its plan objective.

    Findings are requested one per objective, in plan order. The label comes
    from the plan itself rather than from the model, which sometimes copies
    the whole "theme: goal" line.
    """
    if len(summary.findings) == len(plan):
        for finding, objective in zip(summary.findings, plan, strict=True):
            finding.objective = objective.theme
    return summary
