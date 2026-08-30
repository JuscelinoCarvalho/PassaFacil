from pydantic import BaseModel, Field


class FlashReviewRequest(BaseModel):
    """Autoavaliação do aluno ao virar o cartão: errei|dificil|bom|facil."""
    rating: str = Field(min_length=1, max_length=10)
