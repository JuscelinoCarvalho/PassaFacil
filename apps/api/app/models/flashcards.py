"""Cartões de recordação ativa (flashcards) com repetição espaçada.

Módulo "Discursivas TCE-SP" — pilar de MEMORIZAÇÃO. A ciência da aprendizagem diz
que decorar par associativo (lei ↔ artigo ↔ mnemônico) responde melhor a
**recordação ativa** (o aluno tenta lembrar antes de ver o verso) + **repetição
espaçada** do que a reconhecimento (múltipla escolha) ou a assistir vídeo.

Reaproveita o motor de memória já existente (`services/scheduler.py`,
`SimpleFsrsScheduler`): o `FlashCardState` guarda exatamente o estado que o
scheduler consome (stability/difficulty/last_review) + `next_review_at`.

Tabelas novas → criadas por `Base.metadata.create_all` (padrão do projeto; NÃO
entram em `_ensure_columns`, que é só para colunas novas em tabelas antigas).
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class FlashCard(UUIDMixin, TimestampMixin, Base):
    """Um cartão de recordação ativa. `frente` = pergunta/deixa; `verso` = resposta.
    `deck` agrupa por tema (ex.: 'nucleo-duro-leis', 'governanca-ti')."""
    __tablename__ = "flash_cards"
    __table_args__ = (UniqueConstraint("deck", "ordem"),)

    deck: Mapped[str] = mapped_column(String(60), index=True)
    ordem: Mapped[int] = mapped_column(Integer, default=0)
    frente: Mapped[str] = mapped_column(Text)             # a deixa (o aluno tenta lembrar)
    verso: Mapped[str] = mapped_column(Text)              # a resposta a memorizar
    lei_ref: Mapped[str | None] = mapped_column(String(200))   # lei + artigo (contexto)
    mnemonic: Mapped[str | None] = mapped_column(String(200))  # mnemônico do fast-track
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)


class FlashCardState(UUIDMixin, TimestampMixin, Base):
    """Estado de memória de UM cartão para UM aluno. Espelha o `MemoryState` do
    scheduler (stability/difficulty/last_review) + agenda (`next_review_at`) e
    contadores. 1 linha por (user, card)."""
    __tablename__ = "flash_card_states"
    __table_args__ = (UniqueConstraint("user_id", "card_id"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    card_id: Mapped[UUID] = mapped_column(ForeignKey("flash_cards.id", ondelete="CASCADE"), index=True)
    stability: Mapped[float | None] = mapped_column(Float)      # S (dias) — None = nunca revisado
    difficulty: Mapped[float | None] = mapped_column(Float)     # D (0..1)
    last_review: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    reps: Mapped[int] = mapped_column(Integer, default=0)       # total de revisões
    lapses: Mapped[int] = mapped_column(Integer, default=0)     # nº de vezes que errou (AGAIN)
    last_rating: Mapped[int | None] = mapped_column(Integer)    # 1..4 (AGAIN..EASY)

    card: Mapped[FlashCard] = relationship()
