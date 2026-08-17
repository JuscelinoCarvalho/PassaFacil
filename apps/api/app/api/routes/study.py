import json
import random
import re
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy import case, func, or_, select, true
from sqlalchemy.orm import selectinload

from app.api.deps import AdminUser, CurrentUser, DbSession, PaidUser
from app.models import (
    Attempt, LearningEvent, Question, QuestionProvenance, ReviewItem, StudyTask, Subject, Topic, TrialEvent
)
from app.schemas.study import AnswerRequest, TestSubmitRequest, TrialEventIn
from app.services.adaptive_engine import default_engine
from app.services.feedback import build_answer_feedback, normalize_confidence

router = APIRouter(prefix="/study", tags=["study"])

# Test-drive: conjunto FIXO de questões (sempre as mesmas), cobrindo 8 matérias
# com dificuldades variadas (Gerais + TI). Aberto ao público, sem login.
TRIAL_KEYS: list[str] = [
    "vunesp-tcesp-2025-q02",  # Português — interpretação (texto "O Sobrado")
    "vun-2025-adm-q13",       # Raciocínio Lógico — porcentagem/desconto
    "vun-2025-q30",           # Legislação e Ética — Tribunais de Contas (CF)
    "vun-2025-adm-q17",       # Segurança da Informação — DoS/DDoS (CID)
    "vun-2025-adm-q20",       # Redes e Infraestrutura — URL/HTTP
    "pf-ti-bd-13",            # Banco de Dados — INNER JOIN
    "pf-ti-gov-05",           # Governança de TI — ITIL (incidente)
    "vun-2025-adm-q37",       # Contratações de TI — Lei 14.133
]

# Nunca deixar esta questão (interpretação longa "O Sobrado") abrir a amostra grátis.
TRIAL_AVOID_FIRST_KEY = "vunesp-tcesp-2025-q02"


def published_filter():
    return or_(
        Question.is_published.is_(True),
        Question.provenance.has(QuestionProvenance.rights_status == "owner_only"),
    )


def _parse_slugs(subjects: str | None) -> list[str]:
    """Aceita 'portugues,logica' (CSV) e devolve lista limpa de slugs."""
    if not subjects:
        return []
    return [part.strip() for part in subjects.split(",") if part.strip()]


def _scope_condition(slugs: list[str], specialty: str | None):
    """Condição de escopo para as questões do simulado.
    - `slugs` (matérias específicas escolhidas) tem prioridade;
    - senão, `specialty` traz as matérias comuns (specialty NULL) + as da especialidade;
    - senão, todas as questões."""
    if slugs:
        return Question.topic.has(Topic.subject.has(Subject.slug.in_(slugs)))
    if specialty:
        return Question.topic.has(
            Topic.subject.has(
                or_(Subject.specialty.is_(None), Subject.specialty == specialty)
            )
        )
    return True


@router.get("/subjects")
def subject_scope(user: CurrentUser, db: DbSession):
    """Lista TODAS as matérias (Subject) com a especialidade e quantas questões
    publicadas cada uma tem (0 para as ainda sem questões). Alimenta o seletor de
    especialidade + matérias do simulado no front."""
    rows = db.execute(
        select(
            Subject.slug,
            Subject.name,
            Subject.category,
            Subject.specialty,
            Subject.display_order,
            func.count(Question.id).filter(published_filter()),
        )
        .outerjoin(Subject.topics)
        .outerjoin(Question, Question.topic_id == Topic.id)
        .group_by(Subject.id)
        .order_by(Subject.display_order, Subject.name)
    ).all()
    return [
        {"slug": slug, "name": name, "category": category, "specialty": specialty, "count": count}
        for slug, name, category, specialty, _order, count in rows
    ]


@router.get("/dashboard")
def dashboard(user: CurrentUser, db: DbSession):
    tasks = db.scalars(
        select(StudyTask)
        .where(StudyTask.user_id == user.id, StudyTask.scheduled_date == date.today())
        .order_by(StudyTask.created_at)
    ).all()
    attempts = db.scalars(select(Attempt).where(Attempt.user_id == user.id)).all()
    total = len(attempts)
    correct = sum(item.is_correct for item in attempts)
    today = date.today()
    # Progresso REAL (cresce conforme responde): cobertura = questões distintas / publicadas.
    distinct_answered = len({a.question_id for a in attempts})
    published_total = db.scalar(select(func.count()).select_from(Question).where(published_filter())) or 0
    coverage = round(distinct_answered * 100 / published_total) if published_total else 0
    # Questões respondidas HOJE (answered_at é UTC-aware; compara na data local do servidor).
    answered_today = sum(
        1 for a in attempts
        if a.answered_at and a.answered_at.astimezone().date() == today
    )
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
    plan = user.subscription.plan.value if user.subscription else "free"
    return {
        "user": {"id": user.id, "full_name": user.full_name, "plan": plan},
        "date": date.today(),
        "stats": {
            "questions_answered": total,
            "accuracy": round(correct * 100 / total) if total else 0,
            "completed_tasks": sum(task.is_completed for task in tasks),
            "total_tasks": len(tasks),
            # Estudo hoje = minutos das tarefas concluídas hoje + estimativa por questões
            # respondidas hoje (~1,5 min/questão). Assim reflete a atividade real, não
            # só o plano fixo (que era do dia do seed e ficava sempre 0).
            "study_minutes": sum(task.duration_minutes for task in tasks if task.is_completed) + round(answered_today * 1.5),
            "answered_today": answered_today,
            "distinct_answered": distinct_answered,
            "published_total": published_total,
            "coverage": coverage,
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
def toggle_task(task_id: UUID, user: CurrentUser, db: DbSession):
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
def questions(
    user: PaidUser, db: DbSession, limit: int = 20,
    subjects: str | None = None, specialty: str | None = None,
):
    scope = _scope_condition(_parse_slugs(subjects), specialty)
    answered_ids = select(Attempt.question_id).where(Attempt.user_id == user.id)
    rows = db.scalars(
        select(Question)
        .where(published_filter(), scope, Question.id.not_in(answered_ids))
        .options(selectinload(Question.topic).selectinload(Topic.subject))
        .limit(min(limit, 50))
    ).all()
    if not rows:
        rows = db.scalars(
            select(Question)
            .where(published_filter(), scope)
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


def _interleave_by_subject(rows: list[Question]) -> list[Question]:
    """Round-robin por matéria: distribui as questões alternando disciplinas
    para que a sessão cubra tudo antes de aprofundar em uma só."""
    buckets: dict[str, list[Question]] = defaultdict(list)
    for item in rows:
        buckets[item.topic.subject.name].append(item)
    for bucket in buckets.values():
        random.shuffle(bucket)
    interleaved: list[Question] = []
    names = sorted(buckets, key=lambda name: -len(buckets[name]))
    while any(buckets[name] for name in names):
        for name in names:
            if buckets[name]:
                interleaved.append(buckets[name].pop())
    return interleaved


_HEAVY_STATEMENT_CHARS = 700


def _is_heavy_first(q: Question) -> bool:
    """Questão 'pesada' para ABRIR uma sessão: enunciado muito longo (texto de
    interpretação). Enunciado médio ~165 chars, então >700 pega só as longas."""
    if q.topic and q.topic.slug and "interpretacao" in q.topic.slug:
        return True
    return len(q.statement or "") > _HEAVY_STATEMENT_CHARS


def _avoid_heavy_first(ordered: list[Question]) -> list[Question]:
    """Se a 1ª questão for pesada (interpretação/texto longo), troca com a primeira
    'leve' seguinte — mantém o resto da ordem. Mesma ideia do teste grátis, para não
    dar uma primeira impressão cansativa."""
    if len(ordered) > 1 and _is_heavy_first(ordered[0]):
        for i in range(1, len(ordered)):
            if not _is_heavy_first(ordered[i]):
                ordered[0], ordered[i] = ordered[i], ordered[0]
                break
    return ordered


@router.get("/practice")
def practice(
    user: PaidUser, db: DbSession, limit: int = 5000,
    subjects: str | None = None, specialty: str | None = None,
    focus: str | None = None,
):
    """Modo Simulado/treino: questões publicadas, intercalando as disciplinas
    (round-robin) para abranger todas as matérias.

    P2 — histórico: as questões AINDA NÃO respondidas vêm primeiro; só depois de
    esgotá-las é que as já respondidas voltam (para reforço), nunca antes. Assim
    o aluno não repete uma questão enquanto houver questão nova no escopo.

    focus='gaps' (P3): treina só os pontos fracos — questões nunca respondidas
    ou que o aluno errou; as que ele já acertou ficam de fora.

    `specialty` restringe às matérias comuns + as da especialidade; `subjects`
    (CSV de slugs) afina para matérias específicas."""
    scope = _scope_condition(_parse_slugs(subjects), specialty)
    rows = db.scalars(
        select(Question)
        .where(published_filter(), scope)
        .options(selectinload(Question.topic).selectinload(Topic.subject))
    ).all()

    # Estado do aluno por questão: nunca respondida / já acertou / já errou.
    attempts = db.execute(
        select(Attempt.question_id, func.bool_or(Attempt.is_correct))
        .where(Attempt.user_id == user.id)
        .group_by(Attempt.question_id)
    ).all()
    ever_correct = {qid for qid, ok in attempts if ok}
    answered_ids = {qid for qid, _ in attempts}

    unanswered = [q for q in rows if q.id not in answered_ids]
    wrong_only = [q for q in rows if q.id in answered_ids and q.id not in ever_correct]
    already_ok = [q for q in rows if q.id in ever_correct]

    if focus == "gaps":
        # Só lacunas: nunca respondidas + as que errou (sem repetir os acertos).
        ordered = _interleave_by_subject(unanswered) + _interleave_by_subject(wrong_only)
    else:
        # P2: novas primeiro; depois erradas; por último as já acertadas (reforço).
        ordered = (
            _interleave_by_subject(unanswered)
            + _interleave_by_subject(wrong_only)
            + _interleave_by_subject(already_ok)
        )

    ordered = _avoid_heavy_first(ordered)
    return [
        {
            "id": item.id,
            "statement": item.statement,
            "options": json.loads(item.options),
            "topic": item.topic.name,
            "subject": item.topic.subject.name,
        }
        for item in ordered[: max(1, min(limit, 5000))]
    ]


@router.get("/results")
def results(
    user: CurrentUser, db: DbSession,
    subjects: str | None = None, specialty: str | None = None,
):
    """Painel de resultados / lacunas (P3). Desempenho por matéria, maiores
    gaps e recomendação (repetir tudo x focar nos gaps), no escopo escolhido.
    Comparação com outros usuários fica preparada para quando houver base."""
    scope = _scope_condition(_parse_slugs(subjects), specialty)

    # Total de questões publicadas por matéria (cobertura) no escopo.
    published_rows = db.execute(
        select(Subject.slug, Subject.name, Subject.specialty, func.count(Question.id))
        .join(Subject.topics)
        .join(Question, Question.topic_id == Topic.id)
        .where(published_filter(), scope)
        .group_by(Subject.id)
    ).all()
    published_by_slug = {
        slug: {"name": name, "specialty": spec, "published": total}
        for slug, name, spec, total in published_rows
    }

    # Desempenho do aluno por matéria (tentativas/acertos/distintas respondidas).
    perf_rows = db.execute(
        select(
            Subject.slug,
            func.count(Attempt.id),
            func.sum(case((Attempt.is_correct.is_(True), 1), else_=0)),
            func.count(func.distinct(Attempt.question_id)),
        )
        .join(Subject.topics)
        .join(Question, Question.topic_id == Topic.id)
        .join(Attempt, Attempt.question_id == Question.id)
        .where(Attempt.user_id == user.id, published_filter(), scope)
        .group_by(Subject.id)
    ).all()
    perf_by_slug = {
        slug: {"attempts": att, "correct": int(right or 0), "distinct": distinct}
        for slug, att, right, distinct in perf_rows
    }

    subjects_out = []
    total_att = total_right = total_pub = total_distinct = 0
    for slug, pub in published_by_slug.items():
        if not pub["published"]:
            continue
        perf = perf_by_slug.get(slug, {"attempts": 0, "correct": 0, "distinct": 0})
        att, right, distinct = perf["attempts"], perf["correct"], perf["distinct"]
        total_att += att
        total_right += right
        total_pub += pub["published"]
        total_distinct += min(distinct, pub["published"])
        subjects_out.append({
            "slug": slug,
            "name": pub["name"],
            "specialty": pub["specialty"],
            "published": pub["published"],
            "answered_distinct": min(distinct, pub["published"]),
            "attempts": att,
            "correct": right,
            "accuracy": round(right * 100 / att) if att else None,
            "coverage": round(min(distinct, pub["published"]) * 100 / pub["published"]),
        })

    # Gaps = matérias com pior aproveitamento (>=3 tentativas) OU baixa cobertura.
    def gap_key(s):
        acc = s["accuracy"]
        if s["attempts"] >= 3 and acc is not None:
            return (0, acc, s["coverage"])          # pior acurácia primeiro
        return (1, s["coverage"], -s["published"])   # depois, menor cobertura
    gaps = sorted(subjects_out, key=gap_key)[:5]

    coverage_pct = round(total_distinct * 100 / total_pub) if total_pub else 0
    all_seen = total_pub > 0 and total_distinct >= total_pub
    return {
        "overall": {
            "attempts": total_att,
            "correct": total_right,
            "accuracy": round(total_right * 100 / total_att) if total_att else 0,
            "published": total_pub,
            "answered_distinct": total_distinct,
            "coverage": coverage_pct,
            "all_questions_seen": all_seen,
        },
        "subjects": sorted(subjects_out, key=lambda s: s["name"]),
        "gaps": [g for g in gaps if g["attempts"] or g["coverage"] < 100],
        "recommendation": (
            "repeat_all" if all_seen else "focus_gaps"
        ),
        "peer_comparison": None,  # reservado: ligar quando houver base de usuários
    }


# Blueprint da Prova Objetiva — Especialidade TI (edital 2026):
# 60 questões Específicas (TI) + 20 Gerais = 80. O simulado espelha essa proporção
# (75% TI / 25% Gerais) e a escala para qualquer `size`.
EXAM_SPECIFIC, EXAM_GENERAL = 60, 20
EXAM_TOTAL = EXAM_SPECIFIC + EXAM_GENERAL


@router.get("/test")
def test_mode(
    user: PaidUser, db: DbSession,
    mode: str = "random", size: int = 20,
    subjects: str | None = None, specialty: str | None = None,
):
    """Modo teste/simulado (P4). Sem gabarito na ida — a correção só sai no
    /test/submit (estilo prova).

    - PROPORÇÃO DA PROVA: 75% Específicas (TI) + 25% Gerais (edital: 60 + 20),
      escalada para `size`. Só se aplica quando o usuário NÃO restringiu matérias
      (`subjects`); com matérias escolhidas, sorteia apenas dentro delas.
    - RODÍZIO: prioriza questões que o usuário AINDA NÃO respondeu; quando o
      estoque de inéditas de um bloco acaba, completa com já vistas — assim o
      simulado percorre todo o banco antes de repetir.
    - mode='fixed' devolve sempre o MESMO conjunto (ordem estável p/ medir evolução);
      nesse modo não há rodízio (o objetivo é comparar desempenho no mesmo teste)."""
    size = max(4, min(size, EXAM_TOTAL))
    slugs = _parse_slugs(subjects)
    scope = _scope_condition(slugs, specialty)
    is_general = Question.topic.has(Topic.subject.has(Subject.category == "general"))
    order_random = mode != "fixed"

    seen_ids: set = set()
    if order_random:  # 'fixed' ignora o histórico para manter o conjunto estável
        seen_ids = set(db.scalars(
            select(Attempt.question_id).where(Attempt.user_id == user.id)
        ).all())

    def fetch(cond):
        stmt = (
            select(Question)
            .where(published_filter(), scope, cond)
            .options(selectinload(Question.topic).selectinload(Topic.subject))
        )
        stmt = stmt.order_by(func.random()) if order_random else stmt.order_by(Question.id)
        return list(db.scalars(stmt).all())

    def draw(cond, n):
        """Sorteia `n` questões do bloco `cond`: inéditas primeiro; se faltarem,
        completa reciclando as já respondidas (rodízio pelo banco inteiro)."""
        if n <= 0:
            return []
        pool = fetch(cond)
        chosen = [q for q in pool if q.id not in seen_ids][:n]
        if len(chosen) < n:
            picked = {q.id for q in chosen}
            chosen += [q for q in pool if q.id not in picked][: n - len(chosen)]
        return chosen

    if slugs:  # usuário escolheu matérias → sorteia dentro do escolhido, sem proporção
        selected = draw(true(), size)
    else:      # simulado amplo → espelha a proporção da prova
        want_general = round(size * EXAM_GENERAL / EXAM_TOTAL)
        want_specific = size - want_general
        selected = draw(is_general, want_general) + draw(~is_general, want_specific)

    selected = _interleave_by_subject(selected)[:size]
    return {
        "mode": "fixed" if mode == "fixed" else "random",
        "total": len(selected),
        "questions": [
            {
                "id": item.id,
                "statement": item.statement,
                "options": json.loads(item.options),
                "topic": item.topic.name,
                "subject": item.topic.subject.name,
            }
            for item in selected
        ],
    }


@router.post("/test/submit")
def test_submit(payload: TestSubmitRequest, user: PaidUser, db: DbSession):
    """Corrige o modo teste de uma vez (simulado). Registra as tentativas (contam
    nos stats/gaps) e devolve o resultado por questão + resumo por matéria."""
    if not payload.answers:
        raise HTTPException(status_code=422, detail="Nenhuma resposta enviada")
    q_ids = [a.question_id for a in payload.answers]
    questions = {
        q.id: q for q in db.scalars(
            select(Question)
            .where(Question.id.in_(q_ids), published_filter())
            .options(selectinload(Question.topic).selectinload(Topic.subject))
        ).all()
    }
    details, by_subject = [], defaultdict(lambda: {"total": 0, "correct": 0})
    correct_count = 0
    for ans in payload.answers:
        q = questions.get(ans.question_id)
        if not q:
            continue
        options = json.loads(q.options)
        if ans.selected_option is None or not (0 <= ans.selected_option < len(options)):
            is_correct = False
        else:
            is_correct = ans.selected_option == q.correct_option
            db.add(Attempt(
                user_id=user.id, question_id=q.id,
                selected_option=ans.selected_option, is_correct=is_correct,
                response_time_seconds=None,
            ))
            if not is_correct:
                review = db.scalar(select(ReviewItem).where(
                    ReviewItem.user_id == user.id, ReviewItem.question_id == q.id))
                if not review:
                    review = ReviewItem(user_id=user.id, question_id=q.id)
                    db.add(review)
                review.due_date = date.today()
                review.interval_days = 1
                review.last_result = False
        correct_count += int(is_correct)
        sub = q.topic.subject.name
        by_subject[sub]["total"] += 1
        by_subject[sub]["correct"] += int(is_correct)
        # Diagnóstico por questão (só após terminar o simulado, spec §16/§17): quando
        # há alternativa válida marcada, anexa why_wrong/misconception detectados.
        valid_pick = ans.selected_option is not None and 0 <= ans.selected_option < len(options)
        diag = build_answer_feedback(db, q, ans.selected_option) if valid_pick else None
        details.append({
            "question_id": q.id,
            "is_correct": is_correct,
            "selected_option": ans.selected_option,
            "correct_option": q.correct_option,
            "explanation": q.explanation,
            "micro_aula": q.topic.description if q.topic else None,
            "why_wrong": diag["why_wrong"] if diag else None,
            "misconception": diag["misconception"] if diag else None,
            "topic": q.topic.name,
            "subject": sub,
        })
    db.commit()
    total = len(details)
    return {
        "total": total,
        "correct": correct_count,
        "accuracy": round(correct_count * 100 / total) if total else 0,
        "by_subject": [
            {"subject": name, "total": v["total"], "correct": v["correct"],
             "accuracy": round(v["correct"] * 100 / v["total"]) if v["total"] else 0}
            for name, v in sorted(by_subject.items())
        ],
        "details": details,
    }


@router.post("/questions/{question_id}/answer")
def answer(question_id: UUID, payload: AnswerRequest, user: PaidUser, db: DbSession):
    question = db.get(Question, question_id)
    if not question or not (
        question.is_published
        or (question.provenance and question.provenance.rights_status == "owner_only")
    ):
        raise HTTPException(status_code=404, detail="Questão não encontrada")
    if payload.selected_option >= len(json.loads(question.options)):
        raise HTTPException(status_code=422, detail="Alternativa inválida")
    # Feedback adaptativo (Fase 2): diagnóstico por alternativa + microaula em camadas.
    feedback = build_answer_feedback(db, question, payload.selected_option)
    is_correct = feedback["is_correct"]
    confidence = normalize_confidence(payload.confidence)
    attempt = Attempt(
        user_id=user.id,
        question_id=question.id,
        selected_option=payload.selected_option,
        is_correct=is_correct,
        response_time_seconds=payload.response_time_seconds,
        confidence=confidence,
        hints_used=payload.hints_used,
        session_id=payload.session_id,
        skill_id=question.primary_skill_id,  # denormalizado (F1); NULL enquanto não classificada
    )
    db.add(attempt)
    # Motor adaptativo (F3): atualiza o estado da habilidade (domínio + memória) e
    # agenda a próxima revisão. No-op se a questão ainda não tem primary_skill.
    evaluation = default_engine.evaluate_attempt(
        db, user.id, question, correct=is_correct, confidence=confidence,
        hints_used=payload.hints_used, response_time_s=payload.response_time_seconds,
    )
    # Evento bruto append-only (spec §34/§35) — base p/ recalibrar o algoritmo depois.
    db.add(LearningEvent(
        user_id=user.id,
        question_id=question.id,
        skill_id=question.primary_skill_id,
        event_type="QUESTION_ANSWERED",
        selected_option=payload.selected_option,
        correct=is_correct,
        confidence=confidence,
        response_time=payload.response_time_seconds,
        hints=payload.hints_used,
        session_id=payload.session_id,
        review_interval=round(evaluation.interval_days) if evaluation.interval_days else None,
        scheduler_state_before=evaluation.scheduler_state_before,
        scheduler_state_after=evaluation.scheduler_state_after,
    ))
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
    return feedback


# ===================== TEST-DRIVE (público, sem login) =====================

def _trial_question_ids(db: DbSession) -> set[UUID]:
    return set(
        db.scalars(
            select(QuestionProvenance.question_id).where(
                QuestionProvenance.external_key.in_(TRIAL_KEYS)
            )
        ).all()
    )


@router.get("/trial")
def trial(db: DbSession):
    """Amostra grátis: as mesmas questões fixas para qualquer visitante, sem login."""
    rows = db.scalars(
        select(Question)
        .join(QuestionProvenance, QuestionProvenance.question_id == Question.id)
        .where(QuestionProvenance.external_key.in_(TRIAL_KEYS), published_filter())
        .options(selectinload(Question.topic).selectinload(Topic.subject))
    ).all()
    by_id = {str(q.id): q for q in rows}
    key_to_id = dict(
        db.execute(
            select(QuestionProvenance.external_key, QuestionProvenance.question_id).where(
                QuestionProvenance.external_key.in_(TRIAL_KEYS)
            )
        ).all()
    )
    ordered = [by_id[str(key_to_id[k])] for k in TRIAL_KEYS if k in key_to_id and str(key_to_id[k]) in by_id]
    # Embaralha a cada acesso e GARANTE que a interpretação longa "O Sobrado" nunca
    # seja a primeira (é cansativa p/ abrir a amostra). A trial/full (SEO) segue fixa.
    random.shuffle(ordered)
    avoid_id = key_to_id.get(TRIAL_AVOID_FIRST_KEY)
    if len(ordered) > 1 and avoid_id is not None and ordered[0].id == avoid_id:
        j = random.randint(1, len(ordered) - 1)
        ordered[0], ordered[j] = ordered[j], ordered[0]
    return [
        {
            "id": item.id,
            "statement": item.statement,
            "options": json.loads(item.options),
            "topic": item.topic.name,
            "subject": item.topic.subject.name,
        }
        for item in ordered
    ]


@router.get("/trial/full")
def trial_full(db: DbSession):
    """Amostra COMPLETA (com gabarito, explicação e micro-aula) — para a página
    pública de 'questões comentadas' indexável pelo Google. Conjunto fixo."""
    rows = db.scalars(
        select(Question)
        .join(QuestionProvenance, QuestionProvenance.question_id == Question.id)
        .where(QuestionProvenance.external_key.in_(TRIAL_KEYS), published_filter())
        .options(selectinload(Question.topic).selectinload(Topic.subject))
    ).all()
    key_to_id = dict(
        db.execute(
            select(QuestionProvenance.external_key, QuestionProvenance.question_id).where(
                QuestionProvenance.external_key.in_(TRIAL_KEYS)
            )
        ).all()
    )
    by_id = {q.id: q for q in rows}
    ordered = [by_id[key_to_id[k]] for k in TRIAL_KEYS if k in key_to_id and key_to_id[k] in by_id]
    return [
        {
            "id": item.id,
            "statement": item.statement,
            "options": json.loads(item.options),
            "correct_option": item.correct_option,
            "explanation": item.explanation,
            "micro_aula": item.topic.description if item.topic else None,
            "topic": item.topic.name,
            "subject": item.topic.subject.name,
        }
        for item in ordered
    ]


@router.post("/trial/{question_id}/answer")
def trial_answer(question_id: UUID, payload: AnswerRequest, db: DbSession):
    """Correção pública apenas para as questões do test-drive. Não registra tentativa."""
    if question_id not in _trial_question_ids(db):
        raise HTTPException(status_code=404, detail="Questão não faz parte do teste grátis")
    question = db.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Questão não encontrada")
    if payload.selected_option >= len(json.loads(question.options)):
        raise HTTPException(status_code=422, detail="Alternativa inválida")
    # Usuário gratuito também recebe o feedback adaptativo (spec §2.1 do doc de acesso);
    # só não persistimos tentativa/evento (test-drive anônimo).
    return build_answer_feedback(db, question, payload.selected_option)


# Telemetria anônima do test-drive — para medir se há gente simulando e até onde vão.
TRIAL_EVENT_TYPES = {
    "trial_start", "question_answered", "results_viewed",
    "discursive_opened", "discursive_submitted", "audio_opened",
}
TRIAL_TEXT_CAP = 8000  # trunca a dissertativa (evita payload gigante/abuso)


@router.post("/trial/event")
def trial_event(payload: TrialEventIn, db: DbSession):
    """Registra um evento ANÔNIMO do teste grátis (sem login, separado dos dados de
    usuário). Best-effort: nunca derruba a resposta do visitante. Só aceita tipos
    conhecidos; trunca textos longos."""
    if payload.event_type not in TRIAL_EVENT_TYPES:
        return {"ok": False}
    data = dict(payload.payload) if isinstance(payload.payload, dict) else {}
    if isinstance(data.get("texto"), str):
        data["texto"] = data["texto"][:TRIAL_TEXT_CAP]
    try:
        db.add(TrialEvent(anon_id=payload.anon_id.strip()[:64], event_type=payload.event_type, payload=data))
        db.commit()
    except Exception:  # noqa: BLE001 — telemetria não deve quebrar a experiência
        db.rollback()
        return {"ok": False}
    return {"ok": True}


# ===================== PILOTO DE ÁUDIO (aulas em áudio, avaliação) =====================
# Serve os MP3 do piloto (voz ElevenLabs) só para revisão. O menu "Áudios" segue "em breve"
# no app — isto NÃO liga a feature; é só uma página para o dono ouvir e aprovar a voz.
_PILOT_DIR = Path(__file__).resolve().parents[3] / "media" / "audio_pilot"


@router.get("/audio-pilot", response_class=HTMLResponse)
def audio_pilot_index():
    if not _PILOT_DIR.is_dir():
        return "<p>Sem áudios ainda.</p>"
    files = sorted(p.name for p in _PILOT_DIR.glob("*.mp3"))
    cmp_files = [f for f in files if not f.startswith("q")]
    q_files = [f for f in files if f.startswith("q")]

    def label(f: str) -> str:
        if f in cmp_files:
            return "Comparação de voz — " + f.replace(".mp3", "").replace("_", " ").title()
        parts = f.replace(".mp3", "").split("_", 1)
        subj = parts[1].replace("_", " ").title() if len(parts) > 1 else ""
        return f"{parts[0].upper()} · {subj}"

    def block(title, group):
        rows = "".join(
            f'<li><span class="lbl">{label(f)}</span>'
            f'<audio controls preload="none" src="/api/v1/study/audio-pilot/{f}"></audio></li>'
            for f in group
        )
        return f"<h2>{title}</h2><ul>{rows}</ul>" if group else ""

    html = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Piloto de áudio · Passa Fácil</title>
<style>
body{{font-family:system-ui,-apple-system,'Segoe UI',sans-serif;max-width:720px;margin:0 auto;padding:24px 16px;background:#f7f6f2;color:#182033}}
h1{{font-size:22px}} h2{{font-size:15px;text-transform:uppercase;letter-spacing:.5px;color:#6f54e8;margin-top:28px}}
ul{{list-style:none;padding:0}} li{{background:#fff;border:1px solid #e8e8ef;border-radius:12px;padding:14px 16px;margin:10px 0}}
.lbl{{display:block;font-weight:700;margin-bottom:8px;font-size:14px}} audio{{width:100%}}
.note{{background:#f3f0ff;border:1px solid #e4dcff;color:#5b46c9;border-radius:10px;padding:12px 14px;font-size:13px;line-height:1.5}}
@media(prefers-color-scheme:dark){{body{{background:#16171c;color:#e7e7ee}}li{{background:#21232c;border-color:#2c2e39}}.note{{background:#221d3a;border-color:#332b57;color:#c3b6f7}}}}
</style></head><body>
<h1>🎧 Piloto de áudio — Passa Fácil</h1>
<div class="note"><b>Idioma:</b> português do Brasil (sempre). O texto é 100% pt-BR.
A voz <b>Brian</b> é o timbre grave disponível no plano Free — pode ter leve sotaque não-nativo.
No plano pago (fim do mês) usaremos a voz <b>nativa brasileira “João Gabriel”</b> para pronúncia autêntica.
Formato: enunciado → “pense por alguns segundos” → resposta + porquê.</div>
{block("Comparação de vozes", cmp_files)}
{block("Piloto — 8 questões do teste grátis (voz Brian)", q_files)}
</body></html>"""
    return html


@router.get("/audio-pilot/{name}")
def audio_pilot_file(name: str):
    if not re.fullmatch(r"[a-z0-9_]+\.mp3", name):
        raise HTTPException(status_code=404, detail="Arquivo inválido")
    fp = _PILOT_DIR / name
    if not fp.is_file():
        raise HTTPException(status_code=404, detail="Áudio não encontrado")
    return FileResponse(fp, media_type="audio/mpeg")


# Títulos amigáveis das 8 questões do teste (ordem fixa q1..q8), pt-BR.
_TRIAL_AUDIO_TITLES = {
    1: "Língua Portuguesa — interpretação",
    2: "Raciocínio Lógico",
    3: "Legislação e Ética",
    4: "Segurança da Informação",
    5: "Redes e Infraestrutura",
    6: "Banco de Dados",
    7: "Governança de TI",
    8: "Contratações de TI",
}


_URL_RE = re.compile(r"(https?://[^\s]+|www\.[^\s]+|[^\s]+\.(?:com|br|gov|org|net|edu|io)(?:/[^\s]*)?)")


def _url_annotation(statement: str | None) -> str:
    """Extrai um endereço do enunciado para mostrar ESCRITO ao lado do nome da aula
    (ler URL em voz alta confunde; ver escrito é claro). Ex.: '(www.tce.sp.gov.br/…)'."""
    m = _URL_RE.search(statement or "")
    if not m:
        return ""
    url = re.sub(r"^https?://", "", m.group(0)).rstrip(".,);")
    host = url.split("/", 1)[0]
    short = host + ("/…" if "/" in url else "")
    return f" ({short})"


@router.get("/trial/audios")
def trial_audios(db: DbSession):
    """Lista pública das aulas em áudio do teste grátis (as 8 questões, voz TTS)."""
    if not _PILOT_DIR.is_dir():
        return []
    # n (q{n}) segue a ordem fixa TRIAL_KEYS; puxa os enunciados p/ anotar URLs no título.
    key_by_n = {i + 1: k for i, k in enumerate(TRIAL_KEYS)}
    stmts = dict(
        db.execute(
            select(QuestionProvenance.external_key, Question.statement)
            .join(Question, Question.id == QuestionProvenance.question_id)
            .where(QuestionProvenance.external_key.in_(TRIAL_KEYS))
        ).all()
    )
    out = []
    for p in sorted(_PILOT_DIR.glob("q*.mp3")):
        m = re.match(r"q(\d+)_", p.name)
        n = int(m.group(1)) if m else 0
        title = _TRIAL_AUDIO_TITLES.get(n, p.stem) + _url_annotation(stmts.get(key_by_n.get(n, "")))
        out.append({"n": n, "title": title, "url": f"/api/v1/study/audio-pilot/{p.name}"})
    # Mesma lógica do simulado: embaralha a cada acesso e NUNCA deixa a interpretação
    # longa (q1, "O Sobrado") como primeira — é pesada para a primeira impressão.
    random.shuffle(out)
    if len(out) > 1 and out[0]["n"] == 1:
        j = random.randint(1, len(out) - 1)
        out[0], out[j] = out[j], out[0]
    return out


_TRIAL_STAGES = [
    ("trial_start", "Iniciou o teste"),
    ("question_answered", "Respondeu ≥1 questão"),
    ("results_viewed", "Viu os resultados"),
    ("discursive_opened", "Abriu a dissertativa"),
    ("discursive_submitted", "Escreveu a dissertativa"),
]


@router.get("/trial/analytics")
def trial_analytics(user: AdminUser, db: DbSession, days: int | None = None):
    """Painel ADMIN da telemetria anônima do teste grátis: funil, questões acessadas
    (com acerto) e os textos escritos na dissertativa demo."""
    stmt = select(TrialEvent).order_by(TrialEvent.created_at)
    if days:
        stmt = stmt.where(TrialEvent.created_at >= datetime.now(UTC) - timedelta(days=days))
    rows = db.scalars(stmt).all()

    visitors = {r.anon_id for r in rows}
    by_type: dict[str, set] = defaultdict(set)
    for r in rows:
        by_type[r.event_type].add(r.anon_id)
    base = len(by_type.get("trial_start", set())) or len(visitors) or 1
    funnel = [
        {"key": k, "label": label, "count": len(by_type.get(k, set())),
         "pct": round(len(by_type.get(k, set())) / base * 100, 1)}
        for k, label in _TRIAL_STAGES
    ]

    q_stats: dict[str, dict] = {}
    for r in rows:
        if r.event_type != "question_answered":
            continue
        d = r.payload or {}
        key = str(d.get("question_id", "?"))
        st = q_stats.setdefault(key, {"subject": d.get("subject", "?"), "total": 0, "correct": 0})
        st["total"] += 1
        if d.get("correct"):
            st["correct"] += 1
    questions = sorted(
        [{"subject": v["subject"], "total": v["total"], "correct": v["correct"],
          "accuracy": round(v["correct"] / v["total"] * 100) if v["total"] else 0}
         for v in q_stats.values()],
        key=lambda x: x["total"], reverse=True,
    )

    subs = [
        {"created_at": r.created_at, "length": len((r.payload or {}).get("texto") or ""),
         "texto": (r.payload or {}).get("texto") or ""}
        for r in rows if r.event_type == "discursive_submitted"
    ]
    subs.sort(key=lambda x: x["created_at"], reverse=True)
    avg = round(sum(s["length"] for s in subs) / len(subs)) if subs else 0

    return {
        "visitors": len(visitors),
        "events": len(rows),
        "first": rows[0].created_at if rows else None,
        "last": rows[-1].created_at if rows else None,
        "funnel": funnel,
        "questions": questions,
        "discursive": {"count": len(subs), "avg_length": avg, "items": subs},
    }
