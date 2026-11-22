import pytest
from fastapi.testclient import TestClient

from app.config import Settings, foundry_base_url, resolve_llm_config
from app.main import create_app


def make_settings(**overrides) -> Settings:
    # _env_file=None isolates tests from any real .env on the machine.
    return Settings(_env_file=None, **overrides)


class TestProviderResolution:
    def test_openai_without_key_is_demo(self):
        cfg = resolve_llm_config(make_settings(openai_api_key=None))
        assert cfg.provider == "openai"
        assert cfg.demo is True

    def test_openai_with_key(self):
        cfg = resolve_llm_config(make_settings(openai_api_key="sk-test", openai_model="gpt-test"))
        assert cfg.demo is False
        assert cfg.model == "gpt-test"
        assert cfg.base_url is None

    def test_openai_compatible_base_url_is_passed_through(self):
        cfg = resolve_llm_config(
            make_settings(openai_api_key="k", openai_base_url="http://localhost:11434/v1")
        )
        assert cfg.base_url == "http://localhost:11434/v1"

    def test_foundry_uses_deployment_and_v1_url(self):
        cfg = resolve_llm_config(
            make_settings(
                llm_provider="foundry",
                foundry_endpoint="https://my-res.openai.azure.com",
                foundry_api_key="az-key",
                foundry_deployment="my-deployment",
            )
        )
        assert cfg.provider == "foundry"
        assert cfg.model == "my-deployment"
        assert cfg.base_url == "https://my-res.openai.azure.com/openai/v1/"
        assert cfg.demo is False

    def test_foundry_without_endpoint_is_demo(self):
        cfg = resolve_llm_config(make_settings(llm_provider="foundry", foundry_api_key="k"))
        assert cfg.demo is True


@pytest.mark.parametrize(
    "endpoint",
    [
        "https://res.openai.azure.com",
        "https://res.openai.azure.com/",
        "https://res.openai.azure.com/openai/v1",
        "https://res.openai.azure.com/openai/v1/",
    ],
)
def test_foundry_base_url_normalisation(endpoint):
    assert foundry_base_url(endpoint) == "https://res.openai.azure.com/openai/v1/"


def test_config_endpoint_never_exposes_the_key():
    app = create_app(
        llm_config=resolve_llm_config(make_settings(openai_api_key="sk-secret")),
        llm=object(),  # never called by /api/config
    )
    response = TestClient(app).get("/api/config")

    assert response.status_code == 200
    assert response.json() == {"provider": "openai", "model": "gpt-5.4-mini", "demo": False}
    assert "sk-secret" not in response.text
