from fastapi.testclient import TestClient

from app.config import LLMConfig
from app.llm.demo import read_tag
from app.main import create_app
from app.prompts import PlannedObjective, PlannerOutput, planner_message


def test_create_interview_generates_a_plan(interview):
    assert interview["status"] == "planning"
    assert interview["topic"] == "AI in the workplace"
    assert len(interview["plan"]) == 4  # default
    assert all(o["theme"] and o["goal"] for o in interview["plan"])
    assert interview["turns"] == []
    assert interview["provider"] == "demo"  # never claims a real model in demo mode


def test_plan_size_follows_num_questions(client):
    for n in (3, 5):
        body = client.post("/api/interviews", json={"topic": "remote work", "num_questions": n})
        assert len(body.json()["plan"]) == n


def test_num_questions_out_of_range_is_rejected(client):
    for n in (2, 6):
        r = client.post("/api/interviews", json={"topic": "remote work", "num_questions": n})
        assert r.status_code == 422


def test_plan_can_be_edited_before_starting(client, interview):
    edited = [
        {"theme": "Tools", "goal": "Learn which AI tools they use."},
        {"theme": "Trust", "goal": "Understand how they verify AI output."},
        {"theme": "Future", "goal": "Explore what they expect next."},
    ]
    r = client.put(f"/api/interviews/{interview['id']}/plan", json={"objectives": edited})
    assert r.status_code == 200
    assert r.json()["plan"] == edited


def test_plan_edit_enforces_size(client, interview):
    r = client.put(
        f"/api/interviews/{interview['id']}/plan",
        json={"objectives": [{"theme": "Only", "goal": "One objective."}]},
    )
    assert r.status_code == 422


def test_unknown_interview_returns_404(client):
    assert client.get("/api/interviews/does-not-exist").status_code == 404


def test_planner_message_tags_user_input():
    message = planner_message("Productivity tools", 3)
    assert read_tag(message, "topic") == "Productivity tools"
    assert read_tag(message, "objective_count") == "3"


class ExtraObjectivesLLM:
    """Simulates a model that ignores the requested count."""

    def generate(self, *, system, user, schema):
        items = [PlannedObjective(theme=f"T{i}", goal=f"Goal {i}") for i in range(7)]
        return PlannerOutput(research_goal="goal", objectives=items)


def test_planner_output_is_trimmed_to_requested_count():
    cfg = LLMConfig(provider="openai", model="m", api_key="k", base_url=None)
    client = TestClient(create_app(llm_config=cfg, llm=ExtraObjectivesLLM()))
    r = client.post("/api/interviews", json={"topic": "x" * 5, "num_questions": 3})
    assert [o["theme"] for o in r.json()["plan"]] == ["T0", "T1", "T2"]
