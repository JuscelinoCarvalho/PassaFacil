import json
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession, PaidUser
from app.models import Attempt, LearningEvent, Question, ReviewItem, Topic
from app.schemas.study import AnswerRequest
from app.services.adaptive_engine import default_engine
from app.services.feedback import normalize_confidence

# Revisões: fluxo de aluno (assinante logado), por-usuário. NÃO é mais owner-only
# (ver docs/adaptive-learning-architecture.md §2.1). Usuário gratuito usa o test-drive.
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
def due_reviews(user: PaidUser, db: DbSession):
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
def answer_review(review_id: UUID, payload: AnswerRequest, user: PaidUser, db: DbSession):
    review = db.scalar(
        select(ReviewItem)
        .where(ReviewItem.id == review_id, ReviewItem.user_id == user.id)
        .options(selectinload(ReviewItem.question).selectinload(Question.topic))
    )
    if not review:
        raise HTTPException(status_code=404, detail="Revisão não encontrada")
    question = review.question
    correct = payload.selected_option == question.correct_option
    review.last_result = correct
    review.last_reviewed_at = datetime.now(UTC)
    if correct:
        review.repetitions += 1
        review.interval_days = min(45, [1, 7, 21, 45][min(review.repetitions, 3)])
    else:
        review.repetitions = 0
        review.interval_days = 1
    review.due_date = date.today() + timedelta(days=review.interval_days)

    # Motor adaptativo também na revisão (recuperação após intervalo — sinal forte de
    # memória). No-op se a questão ainda não tem primary_skill.
    confidence = normalize_confidence(payload.confidence)
    evaluation = default_engine.evaluate_attempt(
        db, user.id, question, correct=correct, confidence=confidence,
        hints_used=payload.hints_used, response_time_s=payload.response_time_seconds,
    )
    db.add(LearningEvent(
        user_id=user.id, question_id=question.id, skill_id=question.primary_skill_id,
        event_type="REVIEW_COMPLETED", selected_option=payload.selected_option,
        correct=correct, confidence=confidence, response_time=payload.response_time_seconds,
        hints=payload.hints_used, session_id=payload.session_id,
        review_interval=round(evaluation.interval_days) if evaluation.interval_days else None,
        scheduler_state_before=evaluation.scheduler_state_before,
        scheduler_state_after=evaluation.scheduler_state_after,
    ))
    db.commit()
    return {
        "is_correct": correct,
        "correct_option": review.question.correct_option,
        "explanation": review.question.explanation,
        "next_review": review.due_date,
    }


@router.get("/errors")
def error_notebook(user: PaidUser, db: DbSession):
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

