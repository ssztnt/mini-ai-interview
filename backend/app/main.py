from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import LLMConfig, Provider, get_settings, resolve_llm_config


def get_llm_config() -> LLMConfig:
    return resolve_llm_config(get_settings())


class ConfigResponse(BaseModel):
    """Public runtime info for the UI badge. Never includes secrets."""

    provider: Provider
    model: str
    demo: bool


def create_app() -> FastAPI:
    app = FastAPI(title="Mini AI Interviewer", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/config", response_model=ConfigResponse, tags=["meta"])
    def read_config(cfg: Annotated[LLMConfig, Depends(get_llm_config)]) -> ConfigResponse:
        return ConfigResponse(provider=cfg.provider, model=cfg.model, demo=cfg.demo)

    return app


app = create_app()
