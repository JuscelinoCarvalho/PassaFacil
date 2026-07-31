import json
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession, get_owner_user
from app.models import Attempt, Question, ReviewItem, Topic
from app.schemas.study import AnswerRequest

router = APIRouter(prefix="/reviews", tags=["reviews"])


def serialize_question(question: Question) -> dict:
    return {
        "id": question.id,
        "statement": question.statement,
        "options": json.loads(question.options),
        "correct_option": question.correct_option,
        "explanation": question.explanation,
        "topic": question.topic.name,
        "subject": question.topic.subject.name,
    }


@router.get("/due")
def due_reviews(db: DbSession):
    user = get_owner_user(db)
    rows = db.scalars(
        select(ReviewItem)
        .where(ReviewItem.user_id == user.id, ReviewItem.due_date <= date.today())
        .options(
            selectinload(ReviewItem.question)
            .selectinload(Question.topic)
            .selectinload(Topic.subject)
        )
        .order_by(ReviewItem.due_date)
    ).all()
    return [
        {
            "review_id": row.id,
            "due_date": row.due_date,
            "interval_days": row.interval_days,
            "repetitions": row.repetitions,
            **serialize_question(row.question),
        }
        for row in rows
    ]


@router.post("/{review_id}/answer")
def answer_review(review_id: UUID, payload: AnswerRequest, db: DbSession):
    user = get_owner_user(db)
    review = db.scalar(
        select(ReviewItem)
        .where(ReviewItem.id == review_id, ReviewItem.user_id == user.id)
        .options(selectinload(ReviewItem.question))
    )
    if not review:
        raise HTTPException(status_code=404, detail="Revisão não encontrada")
    correct = payload.selected_option == review.question.correct_option
    review.last_result = correct
    review.last_reviewed_at = datetime.now(UTC)
    if correct:
        review.repetitions += 1
        review.interval_days = min(45, [1, 7, 21, 45][min(review.repetitions, 3)])
    else:
        review.repetitions = 0
        review.interval_days = 1
    review.due_date = date.today() + timedelta(days=review.interval_days)
    db.commit()
    return {
        "is_correct": correct,
        "correct_option": review.question.correct_option,
        "explanation": review.question.explanation,
        "next_review": review.due_date,
    }


@router.get("/errors")
def error_notebook(db: DbSession):
    user = get_owner_user(db)
    wrong_attempts = db.scalars(
        select(Attempt)
        .where(Attempt.user_id == user.id, Attempt.is_correct.is_(False))
        .options(
            selectinload(Attempt.question)
            .selectinload(Question.topic)
            .selectinload(Topic.subject)
        )
        .order_by(Attempt.answered_at.desc())
    ).all()
    seen: set[UUID] = set()
    result = []
    for attempt in wrong_attempts:
        if attempt.question_id in seen:
            continue
        seen.add(attempt.question_id)
        result.append({
            "attempt_id": attempt.id,
            "selected_option": attempt.selected_option,
            "answered_at": attempt.answered_at,
            **serialize_question(attempt.question),
        })
    return result

