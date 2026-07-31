import json
import random
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession, get_owner_user
from app.models import Question, QuestionProvenance, Simulation, SimulationAnswer, Topic
from app.schemas.simulation import SimulationAnswerRequest

router = APIRouter(prefix="/simulations", tags=["simulations"])


def owner_question_filter():
    return or_(
        Question.is_published.is_(True),
        Question.provenance.has(QuestionProvenance.rights_status == "owner_only"),
    )


def simulation_payload(simulation: Simulation) -> dict:
    ordered = sorted(simulation.answers, key=lambda item: item.display_order)
    return {
        "id": simulation.id,
        "title": simulation.title,
        "status": simulation.status,
        "duration_minutes": simulation.duration_minutes,
        "started_at": simulation.started_at,
        "finished_at": simulation.finished_at,
        "answered": sum(item.selected_option is not None for item in ordered),
        "total": len(ordered),
        "questions": [
            {
                "answer_id": item.id,
                "question_id": item.question_id,
                "display_order": item.display_order,
                "selected_option": item.selected_option,
                "statement": item.question.statement,
                "options": json.loads(item.question.options),
                "subject": item.question.topic.subject.name,
                "topic": item.question.topic.name,
            }
            for item in ordered
        ],
    }


@router.post("", status_code=201)
def create_simulation(db: DbSession):
    user = get_owner_user(db)
    questions = list(db.scalars(select(Question).where(owner_question_filter())).all())
    if not questions:
        raise HTTPException(status_code=409, detail="Não há questões publicadas")
    random.shuffle(questions)
    simulation = Simulation(
        user_id=user.id,
        title=f"Simulado diagnóstico #{datetime.now().strftime('%d%m%H%M')}",
        duration_minutes=max(15, len(questions) * 3),
    )
    simulation.answers = [
        SimulationAnswer(question_id=question.id, display_order=index)
        for index, question in enumerate(questions)
    ]
    db.add(simulation)
    db.commit()
    return get_simulation(simulation.id, db)


@router.get("/latest")
def latest_simulation(db: DbSession):
    user = get_owner_user(db)
    simulation = db.scalar(
        select(Simulation)
        .where(Simulation.user_id == user.id)
        .options(
            selectinload(Simulation.answers)
            .selectinload(SimulationAnswer.question)
            .selectinload(Question.topic)
            .selectinload(Topic.subject)
        )
        .order_by(Simulation.created_at.desc())
    )
    return simulation_payload(simulation) if simulation else None


@router.get("/{simulation_id}")
def get_simulation(simulation_id: UUID, db: DbSession):
    user = get_owner_user(db)
    simulation = db.scalar(
        select(Simulation)
        .where(Simulation.id == simulation_id, Simulation.user_id == user.id)
        .options(
            selectinload(Simulation.answers)
            .selectinload(SimulationAnswer.question)
            .selectinload(Question.topic)
            .selectinload(Topic.subject)
        )
    )
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulado não encontrado")
    return simulation_payload(simulation)


@router.post("/{simulation_id}/questions/{question_id}")
def save_answer(
    simulation_id: UUID,
    question_id: UUID,
    payload: SimulationAnswerRequest,
    db: DbSession,
):
    user = get_owner_user(db)
    answer = db.scalar(
        select(SimulationAnswer)
        .join(Simulation)
        .where(
            SimulationAnswer.simulation_id == simulation_id,
            SimulationAnswer.question_id == question_id,
            Simulation.user_id == user.id,
            Simulation.status == "in_progress",
        )
        .options(selectinload(SimulationAnswer.question))
    )
    if not answer:
        raise HTTPException(status_code=404, detail="Questão do simulado não encontrada")
    answer.selected_option = payload.selected_option
    answer.is_correct = payload.selected_option == answer.question.correct_option
    answer.answered_at = datetime.now(UTC)
    db.commit()
    return {"saved": True}


@router.post("/{simulation_id}/finish")
def finish_simulation(simulation_id: UUID, db: DbSession):
    user = get_owner_user(db)
    simulation = db.scalar(
        select(Simulation)
        .where(Simulation.id == simulation_id, Simulation.user_id == user.id)
        .options(selectinload(Simulation.answers).selectinload(SimulationAnswer.question))
    )
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulado não encontrado")
    simulation.status = "finished"
    simulation.finished_at = datetime.now(UTC)
    answered = [item for item in simulation.answers if item.selected_option is not None]
    correct = sum(item.is_correct is True for item in answered)
    db.commit()
    return {
        "total": len(simulation.answers),
        "answered": len(answered),
        "correct": correct,
        "accuracy": round(correct * 100 / len(simulation.answers)),
    }
