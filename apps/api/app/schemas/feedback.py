from typing import Literal

from pydantic import BaseModel, EmailStr, Field

FeedbackCategory = Literal["ajuda", "reclamacao", "sugestao", "elogio", "outro"]


class FeedbackRequest(BaseModel):
    category: FeedbackCategory = "ajuda"
    message: str = Field(min_length=5, max_length=5000)
    contact_email: EmailStr | None = None
    page: str | None = Field(default=None, max_length=255)


class FeedbackResponse(BaseModel):
    ok: bool
