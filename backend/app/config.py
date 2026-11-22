"""Application settings and LLM provider resolution.

Settings are read from environment variables, or from a `.env` file at the
repository root. Exactly one provider is active at a time:

- ``openai``  – api.openai.com, or any OpenAI-compatible API via ``OPENAI_BASE_URL``
- ``foundry`` – a model deployed in Microsoft Foundry (OpenAI v1 endpoint)

If the active provider has no API key, the app runs in **demo mode** with
canned responses, so the full UI can be explored without any credentials.
"""

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent

Provider = Literal["openai", "foundry"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: Provider = "openai"

    # OpenAI (or any OpenAI-compatible provider)
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-5.4-mini"

    # Microsoft Foundry
    foundry_endpoint: str | None = None
    foundry_api_key: str | None = None
    foundry_deployment: str = "gpt-5.4-mini"

    data_dir: Path = BACKEND_DIR / "data" / "interviews"
    cors_origins: list[str] = ["http://localhost:5173"]


@dataclass(frozen=True)
class LLMConfig:
    """Everything the LLM client needs, after provider resolution."""

    provider: Provider
    model: str
    api_key: str | None
    base_url: str | None

    @property
    def demo(self) -> bool:
        return not self.api_key


def foundry_base_url(endpoint: str) -> str:
    """Normalise a Foundry resource endpoint to its OpenAI v1 base URL.

    Accepts ``https://<resource>.openai.azure.com`` (with or without a trailing
    slash or ``/openai/v1``) and returns ``.../openai/v1/``.
    """
    url = endpoint.strip().rstrip("/")
    if not url.endswith("/openai/v1"):
        url += "/openai/v1"
    return url + "/"


def resolve_llm_config(settings: Settings) -> LLMConfig:
    if settings.llm_provider == "foundry":
        has_endpoint = bool(settings.foundry_endpoint)
        return LLMConfig(
            provider="foundry",
            model=settings.foundry_deployment,
            api_key=settings.foundry_api_key if has_endpoint else None,
            base_url=foundry_base_url(settings.foundry_endpoint) if has_endpoint else None,
        )
    return LLMConfig(
        provider="openai",
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
