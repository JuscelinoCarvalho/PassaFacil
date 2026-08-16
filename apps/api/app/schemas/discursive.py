from uuid import UUID

from pydantic import BaseModel, Field


class DiscursiveSubmitRequest(BaseModel):
    texto_resposta: str = Field(min_length=1, max_length=8000)


class SelfAssessRequest(BaseModel):
    # {codigo_do_criterio: pontos_atribuidos_pelo_aluno}
    scores: dict[str, float] = Field(default_factory=dict)
