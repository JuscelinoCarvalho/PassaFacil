"""ReviewQueue + TransferQuestionSelector (Fase 3, spec §14/§9).

Monta a fila de estudo priorizando o que o aluno está prestes a perder e o que o fará
ganhar mais pontos — a partir do `UserSkillState` (memória/domínio) alimentado pelo
AdaptiveLearningEngine. Desacoplado da UI (spec §57): as rotas só consomem `build()`.

Prioridade (spec §14): 1) conhecimento vencido/em risco; 2) habilidades frágeis;
3) erros conceituais de alta confiança; 4) consolidação; 5) relevância no edital;
6) transferência; 7) conteúdo novo. Sempre termina com conteúdo novo, então a fila
nunca fica vazia mesmo com poucas habilidades classificadas (degrada gracioso).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.models import Attempt, Question, Skill, Topic, UserSkillState
from app.models.adaptive import SkillState
from app.services.scheduler import MemoryScheduler, MemoryState, _as_utc, default_scheduler

# Estados que entram na fila mesmo sem estar "vencidos" pelo relógio.
AT_RISK_STATES = {SkillState.FRAGILE.value, SkillState.LAPSED.value}


@dataclass
class QueueItem:
    question: Question
    reason: str            # "review" | "fragile" | "new"
    skill_code: str | None = None
    skill_name: str | None = None
    priority: float = 0.0


def _serialize(item: QueueItem) -> dict:
    q = item.question
    return {
        "id": q.id,
        "statement": q.statement,
        "options": json.loads(q.options),
        "topic": q.topic.name if q.topic else None,
        "subject": q.topic.subject.name if q.topic and q.topic.subject else None,
        "reason": item.reason,
        "skill": ({"code": item.skill_code, "name": item.skill_name} if item.skill_code else None),
    }


def _published():
    from app.models import QuestionProvenance
    return or_(
        Question.is_published.is_(True),
        Question.provenance.has(QuestionProvenance.rights_status == "owner_only"),
    )


class TransferQuestionSelector:
    """Escolhe uma questão DIFERENTE da mesma habilidade (spec §9) — para testar se o
    aluno aprendeu o princípio, não decorou a questão. Prefere questões que ele nunca
    respondeu; evita repetir a questão de origem."""

    def select(
        self, db, user_id, skill_id, *, exclude_question_id=None, answered_ids: set | None = None
    ) -> Question | None:
        if answered_ids is None:
            answered_ids = set(db.scalars(
                select(Attempt.question_id).where(Attempt.user_id == user_id)
            ).all())
        rows = db.scalars(
            select(Question)
            .where(Question.primary_skill_id == skill_id, _published())
            .options(selectinload(Question.topic).selectinload(Topic.subject))
        ).all()
        candidates = [q for q in rows if q.id != exclude_question_id]
        if not candidates:
            return None
        # nunca respondidas primeiro (transferência real); senão, reforço.
        fresh = [q for q in candidates if q.id not in answered_ids]
        pool = fresh or candidates
        return pool[0]


class ReviewQueue:
    def __init__(self, scheduler: MemoryScheduler | None = None) -> None:
        self.scheduler = scheduler or default_scheduler
        self.selector = TransferQuestionSelector()

    def _priority(self, st: UserSkillState, skill: Skill | None, now: datetime) -> float:
        """Score de urgência (maior = mais prioritário) combinando os fatores da §14."""
        score = 0.0
        if st.next_review_at is not None:
            overdue_days = (now - _as_utc(st.next_review_at)).total_seconds() / 86400.0
            if overdue_days >= 0:
                score += 10.0 + overdue_days          # vencido: quanto mais atrasado, mais urgente
        if st.state == SkillState.LAPSED.value:
            score += 8.0
        elif st.state == SkillState.FRAGILE.value:
            score += 6.0
        score += 3.0 * (st.high_confidence_errors or 0)   # erro conceitual de alta confiança
        if st.state == SkillState.CONSOLIDATING.value:
            score += 2.0
        if skill is not None:
            score += 0.5 * (skill.exam_relevance or 3)     # peso no edital
        # retrievabilidade atual baixa = mais em risco
        r = self.scheduler.retrievability(
            MemoryState(st.memory_stability, st.difficulty_estimate, st.last_seen_at), now
        )
        if r is not None:
            score += (1.0 - r) * 4.0
        return score

    def due_skill_count(self, db, user_id, now: datetime | None = None) -> int:
        """Quantas habilidades estão vencidas/em risco (para 'Memória de hoje')."""
        now = now or datetime.now(timezone.utc)
        rows = db.scalars(
            select(UserSkillState).where(
                UserSkillState.user_id == user_id,
                or_(UserSkillState.next_review_at <= now, UserSkillState.state.in_(AT_RISK_STATES)),
            )
        ).all()
        return len(rows)

    def build(self, db, user_id, *, limit: int = 15, now: datetime | None = None) -> list[dict]:
        now = now or datetime.now(timezone.utc)
        answered_ids = set(db.scalars(
            select(Attempt.question_id).where(Attempt.user_id == user_id)
        ).all())

        # 1) habilidades vencidas/em risco, ordenadas por prioridade
        states = db.scalars(
            select(UserSkillState)
            .where(
                UserSkillState.user_id == user_id,
                or_(UserSkillState.next_review_at <= now, UserSkillState.state.in_(AT_RISK_STATES)),
            )
            .options(selectinload(UserSkillState.skill))
        ).all()
        scored = sorted(states, key=lambda s: self._priority(s, s.skill, now), reverse=True)

        items: list[QueueItem] = []
        used_qids: set = set()
        for st in scored:
            if len(items) >= limit:
                break
            q = self.selector.select(db, user_id, st.skill_id, answered_ids=answered_ids)
            if not q or q.id in used_qids:
                continue
            used_qids.add(q.id)
            reason = "fragile" if st.state in AT_RISK_STATES else "review"
            items.append(QueueItem(
                question=q, reason=reason,
                skill_code=st.skill.code if st.skill else None,
                skill_name=st.skill.name if st.skill else None,
            ))

        # 2) completa com conteúdo novo (nunca respondido) até o limite
        if len(items) < limit:
            fresh = db.scalars(
                select(Question)
                .where(_published(), Question.id.not_in(answered_ids | used_qids))
                .options(selectinload(Question.topic).selectinload(Topic.subject))
                .order_by(func.random())
                .limit(limit - len(items))
            ).all()
            for q in fresh:
                items.append(QueueItem(question=q, reason="new"))

        return [_serialize(it) for it in items[:limit]]


default_review_queue = ReviewQueue()
