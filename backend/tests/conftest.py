import pytest
from fastapi.testclient import TestClient

from app.config import LLMConfig, get_settings
from app.llm.demo import DemoClient
from app.main import create_app

DEMO_CONFIG = LLMConfig(provider="openai", model="demo-model", api_key=None, base_url=None)


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """Never let tests write into the real data/interviews folder."""
    monkeypatch.setattr(get_settings(), "data_dir", tmp_path / "interviews")
    return tmp_path / "interviews"


@pytest.fixture
def client() -> TestClient:
    """An API client running fully offline on the demo LLM."""
    return TestClient(create_app(llm_config=DEMO_CONFIG, llm=DemoClient()))


@pytest.fixture
def interview(client: TestClient) -> dict:
    response = client.post("/api/interviews", json={"topic": "AI in the workplace"})
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def answered(client: TestClient, interview: dict) -> dict:
    """An interview with every plan question answered, ready to summarise."""
    client.post(f"/api/interviews/{interview['id']}/start")
    answers = [
        "I use ChatGPT daily to draft emails and it saves me a lot of time.",
        "Honestly the hallucinations are frustrating, I always double check facts.",
        "My team writes reports twice as fast now, which is great.",
        "I hope it gets more reliable, but I worry about junior roles disappearing.",
    ]
    body = None
    for text in answers[: len(interview["plan"])]:
        body = client.post(f"/api/interviews/{interview['id']}/answers", json={"answer": text})
    return body.json()
