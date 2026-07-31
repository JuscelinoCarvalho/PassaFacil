import json
from datetime import UTC, date, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession, get_owner_user
from app.models import (
    Attempt, Question, QuestionProvenance, ReviewItem, StudyTask, Subject, Topic, User
)
from app.schemas.study import AnswerRequest

router = APIRouter(prefix="/study", tags=["study"])


def owner(db: DbSession) -> User:
    return get_owner_user(db)


def owner_question_filter():
    return or_(
        Question.is_published.is_(True),
        Question.provenance.has(QuestionProvenance.rights_status == "owner_only"),
    )


@router.get("/dashboard")
def dashboard(db: DbSession):
    user = owner(db)
    tasks = db.scalars(
        select(StudyTask)
        .where(StudyTask.user_id == user.id, StudyTask.scheduled_date == date.today())
        .order_by(StudyTask.created_at)
    ).all()
    attempts = db.scalars(select(Attempt).where(Attempt.user_id == user.id)).all()
    total = len(attempts)
    correct = sum(item.is_correct for item in attempts)
    subject_rows = db.execute(
        select(
            Subject.name,
            func.count(Attempt.id),
            func.sum(case((Attempt.is_correct.is_(True), 1), else_=0)),
        )
        .join(Subject.topics)
        .join(Question)
        .join(Attempt)
        .where(Attempt.user_id == user.id)
        .group_by(Subject.id)
    ).all() if total else []
    performance = [
        {"name": name, "attempts": count, "accuracy": round((right or 0) * 100 / count)}
        for name, count, right in subject_rows
    ]
    return {
        "user": {"id": user.id, "full_name": user.full_name, "plan": "pro"},
        "date": date.today(),
        "stats": {
            "questions_answered": total,
            "accuracy": round(correct * 100 / total) if total else 0,
            "completed_tasks": sum(task.is_completed for task in tasks),
            "total_tasks": len(tasks),
            "study_minutes": sum(task.duration_minutes for task in tasks if task.is_completed),
        },
        "tasks": [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "activity_type": task.activity_type,
                "duration_minutes": task.duration_minutes,
                "is_completed": task.is_completed,
            }
            for task in tasks
        ],
        "performance": performance,
    }


@router.patch("/tasks/{task_id}/toggle")
def toggle_task(task_id: UUID, db: DbSession):
    user = owner(db)
    task = db.scalar(
        select(StudyTask).where(StudyTask.id == task_id, StudyTask.user_id == user.id)
    )
    if not task:
        raise HTTPException(status_code=404, detail="Atividade não encontrada")
    task.is_completed = not task.is_completed
    task.completed_at = datetime.now(UTC) if task.is_completed else None
    db.commit()
    return {"id": task.id, "is_completed": task.is_completed}


@router.get("/questions")
def questions(db: DbSession, limit: int = 20):
    user = owner(db)
    answered_ids = select(Attempt.question_id).where(Attempt.user_id == user.id)
    rows = db.scalars(
        select(Question)
        .where(owner_question_filter(), Question.id.not_in(answered_ids))
        .options(selectinload(Question.topic).selectinload(Topic.subject))
        .limit(min(limit, 50))
    ).all()
    if not rows:
        rows = db.scalars(
            select(Question)
            .where(owner_question_filter())
            .options(selectinload(Question.topic).selectinload(Topic.subject))
            .limit(min(limit, 50))
        ).all()
    return [
        {
            "id": item.id,
            "statement": item.statement,
            "options": json.loads(item.options),
            "topic": item.topic.name,
            "subject": item.topic.subject.name,
        }
        for item in rows
    ]


@router.post("/questions/{question_id}/answer")
def answer(question_id: UUID, payload: AnswerRequest, db: DbSession):
    user = owner(db)
    question = db.get(Question, question_id)
    if not question or not (
        question.is_published
        or (question.provenance and question.provenance.rights_status == "owner_only")
    ):
        raise HTTPException(status_code=404, detail="Questão não encontrada")
    if payload.selected_option >= len(json.loads(question.options)):
        raise HTTPException(status_code=422, detail="Alternativa inválida")
    is_correct = payload.selected_option == question.correct_option
    attempt = Attempt(
        user_id=user.id,
        question_id=question.id,
        selected_option=payload.selected_option,
        is_correct=is_correct,
        response_time_seconds=payload.response_time_seconds,
    )
    db.add(attempt)
    review = db.scalar(
        select(ReviewItem).where(
            ReviewItem.user_id == user.id, ReviewItem.question_id == question.id
        )
    )
    if not is_correct:
        if not review:
            review = ReviewItem(user_id=user.id, question_id=question.id)
            db.add(review)
        review.due_date = date.today()
        review.interval_days = 1
        review.last_result = False
    db.commit()
    return {
        "is_correct": is_correct,
        "correct_option": question.correct_option,
        "explanation": question.explanation,
    }
