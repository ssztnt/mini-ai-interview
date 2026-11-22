"""Application factory: wires config → LLM client → service → routes."""

import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import router
from app.config import LLMConfig, get_settings, resolve_llm_config
from app.llm import LLMClient, LLMError, OpenAIClient
from app.llm.demo import DemoClient
from app.services import InterviewNotFound, InterviewService, InvalidState
from app.storage import InMemoryInterviewRepository, JsonInterviewStore

logger = logging.getLogger(__name__)


def build_llm(config: LLMConfig) -> LLMClient:
    return DemoClient() if config.demo else OpenAIClient(config)


def error(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"detail": message})


def create_app(
    *,
    llm_config: LLMConfig | None = None,
    llm: LLMClient | None = None,
    store: JsonInterviewStore | None = None,
) -> FastAPI:
    settings = get_settings()
    llm_config = llm_config or resolve_llm_config(settings)
    llm = llm or build_llm(llm_config)

    app = FastAPI(
        title="Mini AI Interviewer",
        version="0.1.0",
        description="Short, adaptive AI-led interviews with an AI-generated summary.",
    )
    app.state.llm_config = llm_config
    store = store or JsonInterviewStore(settings.data_dir)
    app.state.service = InterviewService(llm, llm_config, InMemoryInterviewRepository(), store)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.exception_handler(InterviewNotFound)
    def _not_found(_: Request, __: InterviewNotFound) -> JSONResponse:
        return error(status.HTTP_404_NOT_FOUND, "Interview not found")

    @app.exception_handler(InvalidState)
    def _invalid_state(_: Request, exc: InvalidState) -> JSONResponse:
        return error(status.HTTP_409_CONFLICT, str(exc))

    @app.exception_handler(LLMError)
    def _llm_error(_: Request, exc: LLMError) -> JSONResponse:
        logger.error("LLM failure: %s", exc)
        return error(status.HTTP_502_BAD_GATEWAY, f"The AI model could not respond: {exc}")

    mode = "demo mode" if llm_config.demo else f"{llm_config.provider} · {llm_config.model}"
    logger.info("Mini AI Interviewer ready (%s)", mode)
    return app


app = create_app()
