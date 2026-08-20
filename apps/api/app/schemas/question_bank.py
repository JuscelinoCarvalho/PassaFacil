from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class ImportQuestion(BaseModel):
    external_key: str | None = Field(default=None, max_length=240)
    topic_slug: str
    statement: str = Field(min_length=10)
    options: list[str] = Field(min_length=2, max_length=10)
    correct_option: int = Field(ge=0, le=9)
    explanation: str | None = None


class ManageQuestionUpdate(BaseModel):
    """Edição de uma questão JÁ publicada (oficina do proprietário). Todos os campos
    são opcionais — só o que vier (exclude_unset) é alterado."""
    statement: str | None = Field(default=None, min_length=5)
    options: list[str] | None = Field(default=None, min_length=2, max_length=10)
    correct_option: int | None = Field(default=None, ge=0, le=9)
    explanation: str | None = None
    micro_lesson: dict | None = None          # camadas: essential(pegadinha/macete...), deep, mastery
    topic_id: str | None = None
    image_url: str | None = None              # nome do arquivo em media/question_assets (ou "" p/ remover)
    is_published: bool | None = None
    review_status: str | None = Field(default=None, max_length=30)


class ImportBatch(BaseModel):
    source_name: str
    source_url: HttpUrl | None = None
    organization: str | None = None
    board: str | None = None
    exam_year: int | None = Field(default=None, ge=1900, le=2100)
    rights_status: Literal["research_only", "owner_only", "licensed", "public_domain", "authorial"]
    import_batch: str | None = None
    questions: list[ImportQuestion] = Field(min_length=1, max_length=5000)

