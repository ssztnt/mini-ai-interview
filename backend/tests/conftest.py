import pytest
from fastapi.testclient import TestClient

from app.config import LLMConfig
from app.llm.demo import DemoClient
from app.main import create_app

DEMO_CONFIG = LLMConfig(provider="openai", model="demo-model", api_key=None, base_url=None)


@pytest.fixture
def client() -> TestClient:
    """An API client running fully offline on the demo LLM."""
    return TestClient(create_app(llm_config=DEMO_CONFIG, llm=DemoClient()))


@pytest.fixture
def interview(client: TestClient) -> dict:
    response = client.post("/api/interviews", json={"topic": "AI in the workplace"})
    assert response.status_code == 201
    return response.json()
