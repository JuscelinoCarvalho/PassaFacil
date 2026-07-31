from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class ImportQuestion(BaseModel):
    external_key: str | None = Field(default=None, max_length=240)
    topic_slug: str
    statement: str = Field(min_length=10)
    options: list[str] = Field(min_length=2, max_length=10)
    correct_option: int = Field(ge=0, le=9)
    explanation: str | None = None


class ImportBatch(BaseModel):
    source_name: str
    source_url: HttpUrl | None = None
    organization: str | None = None
    board: str | None = None
    exam_year: int | None = Field(default=None, ge=1900, le=2100)
    rights_status: Literal["research_only", "owner_only", "licensed", "public_domain", "authorial"]
    import_batch: str | None = None
    questions: list[ImportQuestion] = Field(min_length=1, max_length=5000)

