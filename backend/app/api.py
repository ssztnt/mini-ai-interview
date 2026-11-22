"""HTTP routes. Thin by design: validate input and delegate to the service."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel

from app.config import LLMConfig, Provider
from app.models import (
    AnswerRequest,
    CreateInterviewRequest,
    Interview,
    InterviewListItem,
    UpdatePlanRequest,
)
from app.services import InterviewService

router = APIRouter(prefix="/api")


def get_service(request: Request) -> InterviewService:
    return request.app.state.service


def get_llm_config(request: Request) -> LLMConfig:
    return request.app.state.llm_config


Service = Annotated[InterviewService, Depends(get_service)]


class ConfigResponse(BaseModel):
    """Public runtime info for the UI badge. Never includes secrets."""

    provider: Provider
    model: str
    demo: bool


@router.get("/config", response_model=ConfigResponse, tags=["meta"])
def read_config(cfg: Annotated[LLMConfig, Depends(get_llm_config)]) -> ConfigResponse:
    return ConfigResponse(provider=cfg.provider, model=cfg.model, demo=cfg.demo)


@router.post(
    "/interviews",
    response_model=Interview,
    status_code=status.HTTP_201_CREATED,
    tags=["interviews"],
)
def create_interview(body: CreateInterviewRequest, service: Service) -> Interview:
    """Create an interview and generate its plan."""
    return service.create(body.topic, body.num_questions)


@router.get("/interviews", response_model=list[InterviewListItem], tags=["interviews"])
def list_interviews(service: Service) -> list[InterviewListItem]:
    """Completed interviews, newest first."""
    return [InterviewListItem.from_interview(i) for i in service.list_completed()]


@router.get("/interviews/{interview_id}", response_model=Interview, tags=["interviews"])
def read_interview(interview_id: str, service: Service) -> Interview:
    return service.get(interview_id)


@router.put("/interviews/{interview_id}/plan", response_model=Interview, tags=["interviews"])
def update_plan(interview_id: str, body: UpdatePlanRequest, service: Service) -> Interview:
    """Replace the plan with the user's edited version (only before starting)."""
    return service.update_plan(interview_id, body.objectives)


@router.post("/interviews/{interview_id}/start", response_model=Interview, tags=["interviews"])
def start_interview(interview_id: str, service: Service) -> Interview:
    """Lock the plan and generate the first question."""
    return service.start(interview_id)


@router.post("/interviews/{interview_id}/answers", response_model=Interview, tags=["interviews"])
def submit_answer(interview_id: str, body: AnswerRequest, service: Service) -> Interview:
    """Store the answer to the open question and generate the next, adapted question."""
    return service.answer(interview_id, body.answer)


@router.post("/interviews/{interview_id}/complete", response_model=Interview, tags=["interviews"])
def complete_interview(interview_id: str, service: Service) -> Interview:
    """Generate the AI summary and classic analysis, then save the interview to disk."""
    return service.complete(interview_id)
