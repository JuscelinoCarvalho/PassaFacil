"""AdaptiveLearningEngine — o cérebro adaptativo (Fase 3 do full remake, spec §36).

Responsabilidade desta primeira fatia: a cada resposta, atualizar o estado do
conhecimento do aluno POR HABILIDADE (`UserSkillState`) — separando DOMÍNIO
(`mastery_score`, evidência de que compreendeu) de MEMÓRIA (`memory_stability`,
`retrievability`, `next_review_at`, delegados ao MemoryScheduler) — e transicionar o
estado (UNSEEN→EXPOSED→LEARNING→CONSOLIDATING→MASTERED, com FRAGILE/LAPSED).

Fica DESACOPLADO da UI e das rotas (spec §57). O endpoint só chama `evaluate_attempt`.
`mastery_score` NÃO é percentual bruto de acertos (spec §11): é uma média móvel da
"qualidade" de cada tentativa (confiança, dica, dificuldade, erro confiante).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select

from app.models import Question, UserSkillState
from app.models.adaptive import SkillState
from app.services.scheduler import (
    MemoryScheduler, MemoryState, Rating, default_scheduler, map_response_to_rating,
)


@dataclass(frozen=True)
class AdaptiveConfig:
    mastery_alpha: float = 0.3          # peso da tentativa nova na média móvel do domínio
    mastered_threshold: float = 0.8
    consolidating_threshold: float = 0.5
    mastered_min_streak: int = 2
    mastered_min_stability: float = 7.0  # dias de retenção p/ considerar "dominado"


@dataclass(frozen=True)
class EvaluationResult:
    """Devolvido ao chamador para alimentar o LearningEvent (spec §35) e a UI."""
    skill_state: UserSkillState | None
    rating: Rating | None = None
    scheduler_state_before: dict | None = None
    scheduler_state_after: dict | None = None
    interval_days: float | None = None


class AdaptiveLearningEngine:
    def __init__(
        self, scheduler: MemoryScheduler | None = None, config: AdaptiveConfig | None = None
    ) -> None:
        self.scheduler = scheduler or default_scheduler
        self.cfg = config or AdaptiveConfig()

    # ------------------------------------------------------------------ #
    def evaluate_attempt(
        self, db, user_id, question: Question, *, correct: bool,
        confidence: str | None = None, hints_used: int = 0,
        response_time_s: int | None = None, is_transfer: bool = False,
        now: datetime | None = None,
    ) -> EvaluationResult:
        """Atualiza o UserSkillState da habilidade primária da questão. Se a questão
        ainda não está classificada (sem `primary_skill_id`), não há o que atualizar
        (degrada gracioso) — a F8 classificará o acervo."""
        skill_id = question.primary_skill_id
        if not skill_id:
            return EvaluationResult(skill_state=None)

        now = now or datetime.now(timezone.utc)
        state = db.scalar(
            select(UserSkillState).where(
                UserSkillState.user_id == user_id, UserSkillState.skill_id == skill_id
            )
        )
        if state is None:
            state = UserSkillState(user_id=user_id, skill_id=skill_id, state=SkillState.UNSEEN.value)
            db.add(state)
            db.flush()  # materializa os defaults (contadores=0, mastery=0.0) na instância

        prev_state = state.state
        prev_last_review = state.last_seen_at  # instante da última revisão (p/ o scheduler)

        # ---- contadores e sinais pedagógicos ----
        state.attempts += 1
        if correct:
            state.correct_attempts += 1
            state.consecutive_successes += 1
            state.consecutive_failures = 0
            state.last_success_at = now
            if confidence in {"chutei", "duvida"}:
                state.low_confidence_corrects += 1  # spec §43
            if is_transfer:
                state.transfer_successes += 1
        else:
            state.wrong_attempts += 1
            state.consecutive_failures += 1
            state.consecutive_successes = 0
            if confidence == "confiante":
                state.high_confidence_errors += 1  # spec §44 (possível misconception consolidado)
        state.first_seen_at = state.first_seen_at or now
        state.last_seen_at = now
        state.last_response_time = response_time_s

        # ---- memória (MemoryScheduler) ----
        rating = map_response_to_rating(
            correct=correct, confidence=confidence, hints_used=hints_used, response_time_s=response_time_s
        )
        mem_before = MemoryState(
            stability=state.memory_stability, difficulty=state.difficulty_estimate,
            last_review=prev_last_review,
        )
        before_snap = _snap(mem_before, self.scheduler, now) if state.memory_stability is not None else None
        outcome = self.scheduler.register_review(mem_before, rating, now=now)
        state.memory_stability = outcome.state.stability
        state.difficulty_estimate = outcome.state.difficulty
        # retrievability guardada = a prob. de recuperar NO momento em que respondeu
        # (None na 1ª vez). A UI/dashboard recalcula a atual a partir de stability+last.
        state.retrievability = outcome.retrievability_before
        state.next_review_at = outcome.next_review_at
        after_snap = _snap(outcome.state, self.scheduler, now)

        # ---- domínio (mastery) ----
        quality = self._attempt_quality(correct, confidence, hints_used, question.difficulty)
        state.mastery_score = round(
            (1 - self.cfg.mastery_alpha) * (state.mastery_score or 0.0) + self.cfg.mastery_alpha * quality, 4
        )

        # ---- máquina de estados ----
        state.state = self._transition(state, prev_state=prev_state, correct=correct)

        return EvaluationResult(
            skill_state=state, rating=rating,
            scheduler_state_before=before_snap, scheduler_state_after=after_snap,
            interval_days=outcome.interval_days,
        )

    # ------------------------------------------------------------------ #
    def _attempt_quality(
        self, correct: bool, confidence: str | None, hints_used: int, difficulty: int | None
    ) -> float:
        """Qualidade [0..1] de UMA tentativa (alimenta a média móvel do domínio).
        Erro confiante é o pior sinal (spec §44); acerto com dica/chute vale menos;
        acertar questão mais difícil vale um pouco mais."""
        if not correct:
            return 0.0 if confidence == "confiante" else 0.1
        base = 1.0
        if hints_used and hints_used > 0:
            base -= 0.3
        if confidence == "chutei":
            base -= 0.45
        elif confidence == "duvida":
            base -= 0.2
        if difficulty:  # 1..5 → fator 0.9 .. 1.1 (não deixa passar de 1)
            base *= 0.85 + 0.05 * max(1, min(5, difficulty))
        return max(0.0, min(1.0, base))

    def _transition(self, state: UserSkillState, *, prev_state: str, correct: bool) -> str:
        """Transição de estado (spec §11), pragmática e documentada — os limiares
        podem ser recalibrados depois com base nos learning_events."""
        mastery = state.mastery_score or 0.0
        strong_memory = (state.memory_stability or 0.0) >= self.cfg.mastered_min_stability
        consolidated = {SkillState.MASTERED.value, SkillState.CONSOLIDATING.value}

        if not correct:
            # Errar algo já consolidado = lapso; caso contrário segue aprendendo.
            if prev_state in consolidated:
                return SkillState.LAPSED.value
            return SkillState.LEARNING.value if state.attempts > 1 else SkillState.EXPOSED.value

        # acerto:
        if prev_state == SkillState.LAPSED.value:
            return SkillState.FRAGILE.value  # recuperou após lapso, ainda não confiável
        if (mastery >= self.cfg.mastered_threshold
                and state.consecutive_successes >= self.cfg.mastered_min_streak
                and strong_memory):
            return SkillState.MASTERED.value
        if mastery >= self.cfg.consolidating_threshold:
            return SkillState.CONSOLIDATING.value
        if state.attempts <= 1:
            return SkillState.EXPOSED.value
        return SkillState.LEARNING.value


def _snap(mem: MemoryState, scheduler: MemoryScheduler, now: datetime) -> dict:
    """Fotografa o estado de memória para o log bruto (JSON-serializável, spec §35)."""
    return {
        "stability": mem.stability,
        "difficulty": mem.difficulty,
        "retrievability": scheduler.retrievability(mem, now),
    }


# Instância padrão do processo.
default_engine = AdaptiveLearningEngine()
