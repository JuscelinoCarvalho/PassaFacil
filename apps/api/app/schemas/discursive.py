from uuid import UUID

from pydantic import BaseModel, Field


class DiscursiveSubmitRequest(BaseModel):
    texto_resposta: str = Field(min_length=1, max_length=8000)


class SelfAssessRequest(BaseModel):
    # {codigo_do_criterio: pontos_atribuidos_pelo_aluno}
    scores: dict[str, float] = Field(default_factory=dict)


class RewriteRequest(BaseModel):
    """Reescrita ativa (Fase 7): o aluno reescreve o trecho de UM critério."""
    codigo: str = Field(min_length=1, max_length=10)
    texto: str = Field(min_length=1, max_length=4000)
