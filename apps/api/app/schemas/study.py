from uuid import UUID

from pydantic import BaseModel, Field


class AnswerRequest(BaseModel):
    selected_option: int = Field(ge=0, le=10)
    response_time_seconds: int | None = Field(default=None, ge=0, le=86400)
    # Fase 2 (modo aprendizagem) — todos opcionais/retrocompatíveis. `confidence` é
    # normalizada no serviço (chutei|duvida|confiante); valores fora disso viram None.
    confidence: str | None = Field(default=None, max_length=20)
    hints_used: int = Field(default=0, ge=0, le=20)
    session_id: str | None = Field(default=None, max_length=64)


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

