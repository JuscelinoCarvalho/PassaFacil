from uuid import UUID

from pydantic import BaseModel, Field


class AnswerRequest(BaseModel):
    selected_option: int = Field(ge=0, le=10)
    response_time_seconds: int | None = Field(default=None, ge=0, le=86400)


class TrialEventIn(BaseModel):
    """Telemetria anônima do teste grátis (sem login)."""
    anon_id: str = Field(min_length=1, max_length=64)
    event_type: str = Field(min_length=1, max_length=40)
    payload: dict = Field(default_factory=dict)


class TestAnswer(BaseModel):
    question_id: UUID
    selected_option: int | None = Field(default=None, ge=0, le=10)


class TestSubmitRequest(BaseModel):
    answers: list[TestAnswer] = Field(default_factory=list, max_length=60)

