from pydantic import BaseModel, Field


class AnswerRequest(BaseModel):
    selected_option: int = Field(ge=0, le=10)
    response_time_seconds: int | None = Field(default=None, ge=0, le=86400)

