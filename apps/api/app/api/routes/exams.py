from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.models import Exam

router = APIRouter(prefix="/exams", tags=["exams"])


@router.get("")
def list_exams(db: DbSession):
    exams = db.scalars(
        select(Exam).where(Exam.is_published.is_(True)).options(selectinload(Exam.subjects))
    ).all()
    return [
        {
            "id": exam.id,
            "slug": exam.slug,
            "name": exam.name,
            "organization": exam.organization,
            "board": exam.board,
            "exam_date": exam.exam_date,
            "subject_count": len(exam.subjects),
        }
        for exam in exams
    ]

