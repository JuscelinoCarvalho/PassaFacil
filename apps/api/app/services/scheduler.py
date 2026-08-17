"""MemoryScheduler — agendamento de memória (repetição espaçada) DESACOPLADO da UI.

Fase 3 do full remake (spec §12/§13). O produto separa **domínio** (compreensão —
tratado no AdaptiveLearningEngine) de **memória** (probabilidade de recuperar depois
de um intervalo — tratada aqui).

Decisão de arquitetura (docs/adaptive-learning-architecture.md §5): NÃO adicionamos
dependência FSRS. Definimos uma interface `MemoryScheduler` e uma implementação
própria estilo-FSRS em Python puro (`SimpleFsrsScheduler`), deixando um *seam* para,
no futuro, plugar `py-fsrs` via um adapter que implemente a mesma interface — sem
tocar no resto do sistema. Os pesos ficam TODOS em `SchedulerConfig` (spec §13:
"os pesos devem ficar configuráveis e não espalhados pelo código").

Modelo de estado da memória (por habilidade): `stability` (S, em dias — quanto tempo
o traço resiste), `difficulty` (D, 0..1 — quão difícil é para o aluno) e o instante
da última revisão. A retrievabilidade R(t) usa a curva de esquecimento do FSRS:

    R(t) = (1 + FACTOR · t/S) ^ DECAY ,  DECAY = -0.5, FACTOR = 19/81

O próximo intervalo é o t em que R cai ao alvo (`target_retention`, ex. 0.9).
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


class Rating(enum.IntEnum):
    """Qualidade da recuperação (spec §13). Ordem crescente importa nos cálculos."""
    AGAIN = 1   # errou
    HARD = 2    # acertou com dificuldade (dica / chute / baixa confiança)
    GOOD = 3    # acertou normalmente
    EASY = 4    # acertou com folga (confiante, sem dica)


@dataclass(frozen=True)
class MemoryState:
    """Estado de memória de uma habilidade para um aluno (imutável; o scheduler
    devolve um novo a cada revisão). `last_review` é timezone-aware (UTC)."""
    stability: float | None = None          # S em dias; None = nunca revisado
    difficulty: float | None = None         # D em 0..1; None = nunca revisado
    last_review: datetime | None = None


@dataclass(frozen=True)
class ReviewOutcome:
    """Resultado de `register_review`: novo estado + quando revisar de novo."""
    state: MemoryState
    next_review_at: datetime
    interval_days: float
    retrievability_before: float | None  # R no momento da revisão (None se 1ª vez)


@dataclass(frozen=True)
class SchedulerConfig:
    """Todos os pesos num só lugar (spec §13). Valores estilo-FSRS, conservadores."""
    decay: float = -0.5
    factor: float = 19.0 / 81.0
    target_retention: float = 0.9
    min_interval_days: float = 1.0
    max_interval_days: float = 365.0
    # Estabilidade inicial (dias) por rating na 1ª exposição.
    initial_stability: dict[int, float] = field(
        default_factory=lambda: {Rating.AGAIN: 0.4, Rating.HARD: 0.9, Rating.GOOD: 2.5, Rating.EASY: 6.0}
    )
    # Dificuldade inicial (0..1) por rating.
    initial_difficulty: dict[int, float] = field(
        default_factory=lambda: {Rating.AGAIN: 0.75, Rating.HARD: 0.6, Rating.GOOD: 0.45, Rating.EASY: 0.3}
    )
    # Ganho de estabilidade em acerto: base por rating (multiplicador extra).
    success_gain: dict[int, float] = field(
        default_factory=lambda: {Rating.HARD: 0.6, Rating.GOOD: 1.4, Rating.EASY: 2.4}
    )
    difficulty_step: float = 0.12     # quanto D anda a cada revisão
    lapse_stability_factor: float = 0.3   # S após erro = S · isto (pós-lapso, menor)
    min_stability: float = 0.2


def map_response_to_rating(
    *, correct: bool, confidence: str | None = None, hints_used: int = 0,
    response_time_s: int | None = None,
) -> Rating:
    """Mapeia a resposta do aluno para AGAIN/HARD/GOOD/EASY (spec §13).

    - ERRO → AGAIN;
    - ACERTO com dica OU chute/baixa confiança → HARD;
    - ACERTO normal → GOOD;
    - ACERTO confiante e sem dica → candidato a EASY.
    O tempo pode ajudar, mas NÃO decide sozinho: uma resposta confiante porém MUITO
    lenta rebaixa EASY→GOOD (não sobe nada por tempo)."""
    if not correct:
        return Rating.AGAIN
    if hints_used and hints_used > 0:
        return Rating.HARD
    if confidence in {"chutei", "duvida"}:
        return Rating.HARD
    if confidence == "confiante":
        # Confiante + sem dica → EASY, salvo se demorou muito (sinal de esforço).
        if response_time_s is not None and response_time_s > 90:
            return Rating.GOOD
        return Rating.EASY
    return Rating.GOOD  # sem sinal de confiança → acerto normal


class MemoryScheduler:
    """Interface (spec §12). Um adapter FSRS futuro implementa os mesmos métodos."""

    def retrievability(self, state: MemoryState, now: datetime | None = None) -> float | None:
        raise NotImplementedError

    def register_review(
        self, state: MemoryState, rating: Rating, now: datetime | None = None
    ) -> ReviewOutcome:
        raise NotImplementedError


class SimpleFsrsScheduler(MemoryScheduler):
    """Implementação própria estilo-FSRS (pura, sem dependências)."""

    def __init__(self, config: SchedulerConfig | None = None) -> None:
        self.cfg = config or SchedulerConfig()

    # ---- curva de esquecimento ----
    def retrievability(self, state: MemoryState, now: datetime | None = None) -> float | None:
        if state.stability is None or state.last_review is None:
            return None
        now = now or datetime.now(timezone.utc)
        elapsed = max(0.0, (now - state.last_review).total_seconds() / 86400.0)
        S = max(self.cfg.min_stability, state.stability)
        r = (1.0 + self.cfg.factor * elapsed / S) ** self.cfg.decay
        return min(1.0, max(0.0, r))

    def _interval_for(self, stability: float) -> float:
        """t em que R(t) = target_retention, dado S."""
        # target = (1 + factor·t/S)^decay  →  t = S/factor · (target^(1/decay) - 1)
        target = self.cfg.target_retention
        t = stability / self.cfg.factor * (target ** (1.0 / self.cfg.decay) - 1.0)
        return min(self.cfg.max_interval_days, max(self.cfg.min_interval_days, t))

    def _clamp_d(self, d: float) -> float:
        return min(1.0, max(0.0, d))

    def register_review(
        self, state: MemoryState, rating: Rating, now: datetime | None = None
    ) -> ReviewOutcome:
        now = now or datetime.now(timezone.utc)
        cfg = self.cfg

        # 1ª exposição desta habilidade
        if state.stability is None or state.last_review is None:
            S = cfg.initial_stability[int(rating)]
            D = cfg.initial_difficulty[int(rating)]
            interval = self._interval_for(S)
            return ReviewOutcome(
                state=MemoryState(stability=S, difficulty=D, last_review=now),
                next_review_at=now + timedelta(days=interval),
                interval_days=interval,
                retrievability_before=None,
            )

        R = self.retrievability(state, now) or 0.0
        S = max(cfg.min_stability, state.stability)
        D = state.difficulty if state.difficulty is not None else 0.5

        if rating == Rating.AGAIN:
            # Lapso: estabilidade cai; dificuldade sobe.
            new_S = max(cfg.min_stability, S * cfg.lapse_stability_factor)
            new_D = self._clamp_d(D + cfg.difficulty_step)
        else:
            # Acerto: ganho de estabilidade MAIOR quando R estava baixo (recuperação
            # "difícil" fixa mais — efeito de espaçamento), quando o rating é alto e
            # quando a dificuldade é baixa. Fórmula estilo-FSRS simplificada.
            gain = cfg.success_gain[int(rating)]
            factor = 1.0 + gain * (1.0 - R) * (1.1 - D)
            new_S = min(cfg.max_interval_days, S * max(1.05, factor))
            drift = cfg.difficulty_step * (Rating.GOOD - rating) / 2.0  # EASY baixa D, HARD sobe
            new_D = self._clamp_d(D + drift)

        interval = self._interval_for(new_S)
        return ReviewOutcome(
            state=MemoryState(stability=new_S, difficulty=new_D, last_review=now),
            next_review_at=now + timedelta(days=interval),
            interval_days=interval,
            retrievability_before=R,
        )


# Instância padrão do processo (sem estado mutável — seguro compartilhar).
default_scheduler = SimpleFsrsScheduler()
