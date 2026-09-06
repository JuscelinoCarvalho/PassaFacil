"""Cartões de recordação ativa (memorização espaçada) — módulo Discursivas.

O aluno estuda cartões frente/verso: tenta lembrar, revela o verso e se
autoavalia (Errei/Difícil/Bom/Fácil). Cada avaliação alimenta o scheduler de
memória (`services/scheduler.py`) que agenda a próxima revisão. Reuso total do
motor FSRS já existente — aqui só há persistência da agenda por (usuário, cartão).
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.api.deps import DbSession, PaidUser
from app.models import FlashCard, FlashCardState
from app.schemas.flashcards import FlashReviewRequest
from app.services.flashcard_review import apply_review, rating_from_label

router = APIRouter(prefix="/flashcards", tags=["flashcards"])

# Teto de cartões por sessão de estudo (foco > volume; evita fadiga).
SESSION_LIMIT = 20
# Teto de cartões NOVOS introduzidos por dia. Repetição espaçada só funciona se o
# material novo entra dosado — sem isso, a fila de revisão vira bola de neve e nada
# se fixa. Ritmo "Intenso" escolhido pelo dono (2026-09-05).
DAILY_NEW_CARDS = 15


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _today_start() -> datetime:
    return _now().replace(hour=0, minute=0, second=0, microsecond=0)


def introduced_today(db, user_id: UUID) -> int:
    """Quantos cartões NOVOS o aluno já introduziu hoje (estado criado hoje). Base do
    teto diário de novos — compartilhado com a 'Memória de hoje'."""
    return db.scalar(
        select(func.count(FlashCardState.id)).where(
            FlashCardState.user_id == user_id,
            FlashCardState.created_at >= _today_start(),
        )
    ) or 0


def remaining_new_today(db, user_id: UUID) -> int:
    """Quantos cartões novos ainda cabem hoje (teto - já introduzidos)."""
    return max(0, DAILY_NEW_CARDS - introduced_today(db, user_id))


def _card_public(card: FlashCard, state: FlashCardState | None) -> dict:
    """Cartão para estudar — SEMPRE traz o verso (recordação ativa é honra do aluno:
    ele tenta lembrar antes de tocar em 'mostrar'; a UI é que esconde o verso)."""
    return {
        "id": card.id,
        "deck": card.deck,
        "frente": card.frente,
        "verso": card.verso,
        "lei_ref": card.lei_ref,
        "mnemonic": card.mnemonic,
        "is_new": state is None or state.last_review is None,
    }


def _due_filter(user_id: UUID):
    """Estados vencidos (next_review_at <= agora)."""
    return (FlashCardState.user_id == user_id) & (
        FlashCardState.next_review_at <= _now()
    )


@router.get("/decks")
def list_decks(user: PaidUser, db: DbSession):
    """Decks publicados + contagem (total / novos / a revisar hoje) para o aluno."""
    rows = db.execute(
        select(FlashCard.deck, func.count(FlashCard.id))
        .where(FlashCard.is_published.is_(True))
        .group_by(FlashCard.deck)
        .order_by(FlashCard.deck)
    ).all()
    out = []
    for deck, total in rows:
        seen = db.scalar(
            select(func.count(FlashCardState.id))
            .join(FlashCard, FlashCard.id == FlashCardState.card_id)
            .where(
                FlashCard.deck == deck,
                FlashCardState.user_id == user.id,
                FlashCardState.last_review.is_not(None),
            )
        ) or 0
        due = db.scalar(
            select(func.count(FlashCardState.id))
            .join(FlashCard, FlashCard.id == FlashCardState.card_id)
            .where(FlashCard.deck == deck, _due_filter(user.id))
        ) or 0
        out.append({
            "deck": deck,
            "total": total,
            "new": max(0, total - seen),
            "due": due,
        })
    return out


@router.get("/today")
def today(user: PaidUser, db: DbSession):
    """Nº de cartões a revisar hoje (vencidos) + novos ainda não vistos — para o
    card 'Cartões de hoje' da home."""
    due = db.scalar(
        select(func.count(FlashCardState.id)).where(_due_filter(user.id))
    ) or 0
    total = db.scalar(
        select(func.count(FlashCard.id)).where(FlashCard.is_published.is_(True))
    ) or 0
    seen = db.scalar(
        select(func.count(FlashCardState.id)).where(
            FlashCardState.user_id == user.id, FlashCardState.last_review.is_not(None)
        )
    ) or 0
    new_available = max(0, total - seen)
    return {
        "due": due,
        # 'new' = só o que cabe HOJE (dose diária), não o backlog inteiro.
        "new": min(new_available, remaining_new_today(db, user.id)),
        "new_backlog": new_available,
    }


@router.get("/study")
def study(user: PaidUser, db: DbSession, deck: str | None = Query(default=None)):
    """Monta a sessão: primeiro os cartões VENCIDOS (recuperação espaçada), depois
    completa com cartões NOVOS (nunca revisados). Nunca vem vazia enquanto houver
    cartão. Teto de SESSION_LIMIT."""
    base = select(FlashCard).where(FlashCard.is_published.is_(True))
    if deck:
        base = base.where(FlashCard.deck == deck)

    # Estados do aluno indexados por card_id.
    states = {
        s.card_id: s
        for s in db.scalars(select(FlashCardState).where(FlashCardState.user_id == user.id)).all()
    }

    cards = db.scalars(base.order_by(FlashCard.deck, FlashCard.ordem)).all()
    now = _now()
    due_cards, new_cards = [], []
    for c in cards:
        st = states.get(c.id)
        if st is None or st.last_review is None:
            new_cards.append(c)
        else:
            nxt = st.next_review_at
            if nxt is not None and nxt.tzinfo is None:
                nxt = nxt.replace(tzinfo=timezone.utc)
            if nxt is None or nxt <= now:
                due_cards.append((nxt or now, c))

    due_cards.sort(key=lambda t: t[0])  # mais atrasados primeiro
    # Novos entram DOSADOS: só o que ainda cabe no teto diário (o resto espera amanhã).
    allow_new = remaining_new_today(db, user.id)
    ordered = [c for _, c in due_cards] + new_cards[:allow_new]
    session = ordered[:SESSION_LIMIT]
    return {
        "due": len(due_cards),
        "new_total": len(new_cards),
        "new_today": min(len(new_cards), allow_new),
        "cards": [_card_public(c, states.get(c.id)) for c in session],
    }


@router.post("/{card_id}/review")
def review(card_id: UUID, payload: FlashReviewRequest, user: PaidUser, db: DbSession):
    """Registra a autoavaliação de um cartão e agenda a próxima revisão."""
    card = db.get(FlashCard, card_id)
    if not card or not card.is_published:
        raise HTTPException(status_code=404, detail="Cartão não encontrado")
    rating = rating_from_label(payload.rating)
    if rating is None:
        raise HTTPException(status_code=422, detail="Avaliação inválida")

    state = db.scalar(
        select(FlashCardState).where(
            FlashCardState.user_id == user.id, FlashCardState.card_id == card.id
        )
    )
    if state is None:
        state = FlashCardState(user_id=user.id, card_id=card.id)
        db.add(state)

    outcome = apply_review(state, rating)
    db.commit()
    return {
        "next_review_at": outcome.next_review_at,
        "interval_days": round(outcome.interval_days, 2),
        "reps": state.reps,
        "lapses": state.lapses,
    }
