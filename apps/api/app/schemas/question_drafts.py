from uuid import UUID

from pydantic import BaseModel


class AssociateDocuments(BaseModel):
    exam_job_id: UUID
    answer_key_job_id: UUID


class DraftUpdate(BaseModel):
    statement: str
    options: list[str]
    correct_option: int | None = None
    topic_id: UUID | None = None
    reviewer_note: str | None = None
    status: str = "pending"


class DraftBulkAction(BaseModel):
    draft_ids: list[UUID]
    action: str
    topic_id: UUID | None = None
