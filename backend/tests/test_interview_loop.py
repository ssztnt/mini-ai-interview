import pytest
from fastapi.testclient import TestClient

from app.config import LLMConfig
from app.llm import LLMError
from app.llm.demo import DemoClient
from app.main import create_app
from app.models import Interview, Objective
from app.prompts import InterviewerOutput, interviewer_message


def start(client, interview):
    r = client.post(f"/api/interviews/{interview['id']}/start")
    assert r.status_code == 200
    return r.json()


def answer(client, interview_id, text="Some thoughtful answer."):
    return client.post(f"/api/interviews/{interview_id}/answers", json={"answer": text})


def test_start_asks_the_first_question(client, interview):
    body = start(client, interview)
    assert body["status"] == "in_progress"
    assert len(body["turns"]) == 1
    assert body["turns"][0]["objective_index"] == 0
    assert body["turns"][0]["question"]
    assert body["turns"][0]["answer"] is None


def test_one_question_per_objective_then_awaiting_summary(client, interview):
    start(client, interview)
    plan_size = len(interview["plan"])
    for i in range(plan_size):
        body = answer(client, interview["id"], f"Answer number {i}").json()
        if i < plan_size - 1:
            assert len(body["turns"]) == i + 2
            assert body["awaiting_summary"] is False
    assert len(body["turns"]) == plan_size
    assert [t["objective_index"] for t in body["turns"]] == list(range(plan_size))
    assert body["awaiting_summary"] is True


def test_answering_after_last_question_is_rejected(client, interview):
    start(client, interview)
    for _ in interview["plan"]:
        answer(client, interview["id"])
    assert answer(client, interview["id"]).status_code == 409


def test_cannot_answer_before_start(client, interview):
    assert answer(client, interview["id"]).status_code == 409


def test_cannot_edit_plan_after_start(client, interview):
    start(client, interview)
    r = client.put(
        f"/api/interviews/{interview['id']}/plan", json={"objectives": interview["plan"]}
    )
    assert r.status_code == 409


def test_empty_answer_is_rejected(client, interview):
    start(client, interview)
    assert answer(client, interview["id"], "").status_code == 422


class FlakyInterviewer(DemoClient):
    """Fails on the 2nd interviewer call only."""

    def __init__(self):
        super().__init__()
        self.calls = 0
        self.register(InterviewerOutput, self._flaky)

    def _flaky(self, user):
        self.calls += 1
        if self.calls == 2:
            raise LLMError("temporary outage")
        return DemoClient._question(user)


def test_llm_failure_leaves_interview_unchanged_so_answer_can_be_retried():
    cfg = LLMConfig(provider="openai", model="m", api_key=None, base_url=None)
    client = TestClient(create_app(llm_config=cfg, llm=FlakyInterviewer()))
    interview = client.post("/api/interviews", json={"topic": "remote work"}).json()
    start(client, interview)

    failed = answer(client, interview["id"], "My first answer")
    assert failed.status_code == 502
    stored = client.get(f"/api/interviews/{interview['id']}").json()
    assert stored["turns"][0]["answer"] is None  # nothing half-saved

    retried = answer(client, interview["id"], "My first answer")
    assert retried.status_code == 200
    assert retried.json()["turns"][0]["answer"] == "My first answer"


@pytest.fixture
def sample_interview() -> Interview:
    interview = Interview(
        topic="Remote work",
        provider="openai",
        model="m",
        research_goal="Understand remote work.",
        plan=[
            Objective(theme="Setup", goal="Learn about their setup."),
            Objective(theme="Focus", goal="Understand how they stay focused."),
            Objective(theme="Future", goal="Explore what they want next."),
        ],
    )
    return interview


def test_interviewer_message_contains_full_context(sample_interview):
    from app.models import Turn

    sample_interview.turns.append(
        Turn(objective_index=0, question="Describe your setup?", answer="A tiny desk.")
    )
    message = interviewer_message(sample_interview, 1)
    assert "<plan>" in message and "3. Future" in message
    assert "A1: A tiny desk." in message  # memory: the full transcript is sent
    assert "<current_objective>\n2. Focus" in message
    assert "Question 2 of 3" in message
