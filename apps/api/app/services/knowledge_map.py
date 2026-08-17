"""Mapa de conhecimento + riscos + erros conceituais (Fase 5, spec §18/§19/§42).

Agrega o `UserSkillState` (domínio/memória) e os `LearningEvent` (erros) do aluno num
retrato acionável, DESACOPLADO da rota/UI (§57). `mastery_score` é uma ESTIMATIVA do
sistema — não apresentar precisão científica falsa (§18).
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import (
    LearningEvent, Misconception, OptionMisconception, Subject, Topic, UserSkillState,
)
from app.models.adaptive import SkillState
from app.services.scheduler import MemoryState, default_scheduler

# Estado interno → rótulo/bucket visual (spec §18). O bucket guia a cor no front.
STATE_UI = {
    SkillState.MASTERED.value:      {"label": "Dominado",           "bucket": "mastered"},
    SkillState.CONSOLIDATING.value: {"label": "Consolidando",       "bucket": "consolidating"},
    SkillState.FRAGILE.value:       {"label": "Frágil",             "bucket": "fragile"},
    SkillState.LAPSED.value:        {"label": "Precisa rever",      "bucket": "fragile"},
    SkillState.LEARNING.value:      {"label": "Precisa estudar",    "bucket": "learning"},
    SkillState.EXPOSED.value:       {"label": "Visto uma vez",      "bucket": "learning"},
    SkillState.UNSEEN.value:        {"label": "Ainda não avaliado", "bucket": "unseen"},
}
AT_RISK = {SkillState.FRAGILE.value, SkillState.LAPSED.value}


def _pct(x: float | None) -> int | None:
    return None if x is None else round(x * 100)


def _retention(state: UserSkillState, now: datetime) -> float | None:
    return default_scheduler.retrievability(
        MemoryState(state.memory_stability, state.difficulty_estimate, state.last_seen_at), now
    )


def build_knowledge_map(db, user_id, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    states = db.scalars(
        select(UserSkillState)
        .where(UserSkillState.user_id == user_id)
        .options(selectinload(UserSkillState.skill))
    ).all()

    # nomes de disciplina/tópico das habilidades vistas
    subj_ids = {s.skill.subject_id for s in states if s.skill and s.skill.subject_id}
    topic_ids = {s.skill.topic_id for s in states if s.skill and s.skill.topic_id}
    subj_name = dict(db.execute(select(Subject.id, Subject.name).where(Subject.id.in_(subj_ids))).all()) if subj_ids else {}
    topic_name = dict(db.execute(select(Topic.id, Topic.name).where(Topic.id.in_(topic_ids))).all()) if topic_ids else {}

    # ---- indicadores (§42) ----
    seen = len(states)
    masteries = [s.mastery_score or 0.0 for s in states]
    retentions = [r for s in states if (r := _retention(s, now)) is not None]
    resp_times = [s.last_response_time for s in states if s.last_response_time]
    indicators = {
        "skills_seen": seen,
        "mastered": sum(1 for s in states if s.state == SkillState.MASTERED.value),
        "consolidating": sum(1 for s in states if s.state == SkillState.CONSOLIDATING.value),
        "fragile": sum(1 for s in states if s.state in AT_RISK),
        "estimated_mastery": round(sum(masteries) / seen * 100) if seen else 0,
        "estimated_retention": round(sum(retentions) / len(retentions) * 100) if retentions else None,
        "transfer_successes": sum(s.transfer_successes or 0 for s in states),
        "high_confidence_errors": sum(s.high_confidence_errors or 0 for s in states),
        "avg_response_time": round(sum(resp_times) / len(resp_times)) if resp_times else None,
    }

    # ---- mapa por disciplina → habilidades (§18) ----
    by_subject: dict = {}
    for s in states:
        sk = s.skill
        subj = subj_name.get(sk.subject_id) if sk else None
        subj = subj or "Sem disciplina"
        bucket = by_subject.setdefault(subj, [])
        ui = STATE_UI.get(s.state, STATE_UI[SkillState.UNSEEN.value])
        bucket.append({
            "code": sk.code if sk else None,
            "name": sk.name if sk else "—",
            "topic": topic_name.get(sk.topic_id) if sk else None,
            "mastery_pct": _pct(s.mastery_score),
            "retention_pct": _pct(_retention(s, now)),
            "state": s.state,
            "label": ui["label"],
            "bucket": ui["bucket"],
            "attempts": s.attempts,
            "wrong_attempts": s.wrong_attempts,
        })
    subjects = [
        {
            "subject": name,
            "mastery_pct": round(sum(sk["mastery_pct"] or 0 for sk in skills) / len(skills)),
            "skills": sorted(skills, key=lambda k: (k["mastery_pct"] or 0)),
        }
        for name, skills in sorted(by_subject.items())
    ]

    # ---- riscos: "o que está me fazendo perder pontos" (§19) ----
    def risk_score(s: UserSkillState) -> float:
        score = (1.0 - (s.mastery_score or 0.0)) * 4.0
        if s.state in AT_RISK:
            score += 3.0
        score += 2.0 * (s.high_confidence_errors or 0)
        r = _retention(s, now)
        if r is not None:
            score += (1.0 - r) * 2.0
        return score

    risk_candidates = [
        s for s in states
        if s.state in AT_RISK or (s.mastery_score or 0.0) < 0.5 or (s.high_confidence_errors or 0) > 0
    ]
    risks = [
        {
            "code": s.skill.code if s.skill else None,
            "name": s.skill.name if s.skill else "—",
            "subject": subj_name.get(s.skill.subject_id) if s.skill else None,
            "mastery_pct": _pct(s.mastery_score),
            "attempts": s.attempts,
            "wrong_attempts": s.wrong_attempts,
            "high_confidence_errors": s.high_confidence_errors,
            "state": s.state,
            "label": STATE_UI.get(s.state, STATE_UI[SkillState.UNSEEN.value])["label"],
        }
        for s in sorted(risk_candidates, key=risk_score, reverse=True)[:5]
    ]

    # ---- erros conceituais recorrentes (§42) ----
    misconceptions = _recurring_misconceptions(db, user_id)

    return {
        "indicators": indicators,
        "subjects": subjects,
        "risks": risks,
        "misconceptions": misconceptions,
    }


def _recurring_misconceptions(db, user_id, limit: int = 5) -> list[dict]:
    """Conta quantas vezes cada misconception reapareceu nas respostas erradas do aluno
    (LearningEvent errado → OptionMisconception da alternativa marcada → Misconception)."""
    wrong = db.execute(
        select(LearningEvent.question_id, LearningEvent.selected_option)
        .where(
            LearningEvent.user_id == user_id,
            LearningEvent.correct.is_(False),
            LearningEvent.selected_option.is_not(None),
        )
    ).all()
    if not wrong:
        return []
    q_ids = {q for q, _ in wrong}
    links = db.scalars(
        select(OptionMisconception)
        .where(OptionMisconception.question_id.in_(q_ids))
        .options(selectinload(OptionMisconception.misconception))
    ).all()
    link_map = {(l.question_id, l.option_index): l for l in links}
    counts: dict = {}
    for q_id, opt in wrong:
        link = link_map.get((q_id, opt))
        if not link or not link.misconception:
            continue
        mis = link.misconception
        entry = counts.setdefault(mis.code, {"code": mis.code, "name": mis.name, "count": 0})
        entry["count"] += 1
    return sorted(counts.values(), key=lambda m: m["count"], reverse=True)[:limit]
