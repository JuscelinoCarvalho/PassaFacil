"""Aplicação de uma revisão de flashcard — cola o cartão no scheduler de memória.

Fino de propósito: a lógica de espaçamento vive toda em `services/scheduler.py`
(`SimpleFsrsScheduler`). Aqui só traduzimos o botão de autoavaliação do aluno
(Errei/Difícil/Bom/Fácil) em `Rating`, montamos o `MemoryState` a partir da linha
persistida, chamamos o scheduler e devolvemos o `ReviewOutcome` para o endpoint
gravar de volta.
"""

from __future__ import annotations

from app.models import FlashCardState
from app.services.scheduler import MemoryState, Rating, ReviewOutcome, default_scheduler

# Botão da UI → qualidade da recuperação (mesma semântica do scheduler §13).
RATING_BY_LABEL: dict[str, Rating] = {
    "errei": Rating.AGAIN,
    "dificil": Rating.HARD,
    "bom": Rating.GOOD,
    "facil": Rating.EASY,
}


def rating_from_label(label: str) -> Rating | None:
    return RATING_BY_LABEL.get((label or "").strip().lower())


def apply_review(state: FlashCardState, rating: Rating) -> ReviewOutcome:
    """Roda o scheduler sobre o estado atual do cartão e ESCREVE de volta em `state`
    (stability/difficulty/last_review/next_review_at + contadores)."""
    outcome = default_scheduler.register_review(
        MemoryState(
            stability=state.stability,
            difficulty=state.difficulty,
            last_review=state.last_review,
        ),
        rating,
    )
    state.stability = outcome.state.stability
    state.difficulty = outcome.state.difficulty
    state.last_review = outcome.state.last_review
    state.next_review_at = outcome.next_review_at
    state.reps = (state.reps or 0) + 1
    if rating == Rating.AGAIN:
        state.lapses = (state.lapses or 0) + 1
    state.last_rating = int(rating)
    return outcome
