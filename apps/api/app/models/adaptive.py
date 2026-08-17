"""Entidades da plataforma adaptativa (Fase 1 do "full remake").

Modelo conceitual (spec `full_remake/full-remake.txt`): questão → habilidade →
resposta → tipo de erro → feedback → intervenção → revisão espaçada →
transferência → domínio. Estas tabelas são o esqueleto de dados dessa jornada.

Decisões (ver docs/adaptive-learning-architecture.md §3/§4):
- Todas as tabelas aqui são NOVAS → criadas por `Base.metadata.create_all` no
  startup. As colunas novas em tabelas EXISTENTES (questions/attempts) ficam em
  `app.main._ensure_columns`.
- Vocabulário controlado (estados, papéis, tipos de relação) é `String` + as
  constantes abaixo — não Enum nativo do Postgres — porque vai evoluir e o projeto
  não usa Alembic (um `ALTER TYPE ADD VALUE` seria doloroso). Validação fica na
  camada de serviço (fases seguintes).
- Nada aqui substitui conteúdo existente; campos novos entram AO LADO dos originais.
"""

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


# --------------------------------------------------------------------------- #
# Vocabulário controlado (armazenado como String; ver docstring do módulo).
# --------------------------------------------------------------------------- #
class SkillRelationType(str, enum.Enum):
    prerequisite_of = "prerequisite_of"
    related_to = "related_to"
    depends_on = "depends_on"
    commonly_confused_with = "commonly_confused_with"


class SkillStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    deprecated = "deprecated"


class QuestionSkillRole(str, enum.Enum):
    primary = "primary"
    secondary = "secondary"


class SkillState(str, enum.Enum):
    """Estados do conhecimento do aluno por habilidade (spec §11)."""
    UNSEEN = "UNSEEN"
    EXPOSED = "EXPOSED"
    LEARNING = "LEARNING"
    CONSOLIDATING = "CONSOLIDATING"
    MASTERED = "MASTERED"
    FRAGILE = "FRAGILE"
    LAPSED = "LAPSED"


class Confidence(str, enum.Enum):
    """Escolha rápida de confiança no modo aprendizagem (spec §6)."""
    chutei = "chutei"
    duvida = "duvida"
    confiante = "confiante"


# Tipos de evento de aprendizagem (spec §34). Guardados como String em
# `learning_events.event_type`; lista aqui só para referência/uso na camada de serviço.
LEARNING_EVENT_TYPES = (
    "QUESTION_PRESENTED", "QUESTION_ANSWERED", "ANSWER_CONFIDENCE", "FEEDBACK_VIEWED",
    "MICROLESSON_OPENED", "DEEP_DIVE_OPENED", "TRANSFER_QUESTION_ANSWERED",
    "LESSON_STARTED", "LESSON_COMPLETED", "AUDIO_CHECKPOINT_ANSWERED",
    "ESSAY_STARTED", "ESSAY_SUBMITTED", "ESSAY_FEEDBACK_VIEWED",
    "ESSAY_REWRITE_SUBMITTED", "REVIEW_COMPLETED",
)


# --------------------------------------------------------------------------- #
# Mapa de conhecimento (spec §2/§3)
# --------------------------------------------------------------------------- #
class Skill(UUIDMixin, TimestampMixin, Base):
    """Habilidade avaliável — nível abaixo de Tópico no mapa de conhecimento.

    Ex.: code=LOG-PROP-NEG-COND, name="Negação da proposição condicional",
    description="Reconhecer e aplicar ¬(P → Q) ≡ P ∧ ¬Q".
    Pré-requisitos e demais relações ficam em `skill_relations`.
    """
    __tablename__ = "skills"

    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    subject_id: Mapped[UUID | None] = mapped_column(ForeignKey("subjects.id", ondelete="SET NULL"), index=True)
    topic_id: Mapped[UUID | None] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"), index=True)
    parent_skill_id: Mapped[UUID | None] = mapped_column(ForeignKey("skills.id", ondelete="SET NULL"))
    difficulty_base: Mapped[float] = mapped_column(Float, default=3.0)
    importance: Mapped[int] = mapped_column(Integer, default=3)       # 1–5 (peso pedagógico)
    exam_relevance: Mapped[int] = mapped_column(Integer, default=3)   # 1–5 (peso no edital)
    status: Mapped[str] = mapped_column(String(20), default=SkillStatus.active.value)

    parent: Mapped["Skill | None"] = relationship(remote_side="Skill.id", backref="children")
    question_links: Mapped[list["QuestionSkill"]] = relationship(
        back_populates="skill", cascade="all, delete-orphan"
    )


class SkillRelation(UUIDMixin, TimestampMixin, Base):
    """Aresta do grafo de habilidades (prerequisite_of/related_to/…). Direcional:
    from_skill --relation_type--> to_skill. Ex.: NEGACAO_CONJUNCAO -prerequisite_of-> DE_MORGAN."""
    __tablename__ = "skill_relations"
    __table_args__ = (UniqueConstraint("from_skill_id", "to_skill_id", "relation_type"),)

    from_skill_id: Mapped[UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), index=True)
    to_skill_id: Mapped[UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), index=True)
    relation_type: Mapped[str] = mapped_column(String(40))

    from_skill: Mapped[Skill] = relationship(foreign_keys=[from_skill_id])
    to_skill: Mapped[Skill] = relationship(foreign_keys=[to_skill_id])


class QuestionSkill(UUIDMixin, Base):
    """N:N questão↔habilidade (spec §3/§5). `role`=primary|secondary; `weight` pondera
    o quanto a questão evidencia a habilidade. Fonte de verdade do mapeamento —
    `questions.primary_skill_id` é apenas um espelho de conveniência."""
    __tablename__ = "question_skills"
    __table_args__ = (UniqueConstraint("question_id", "skill_id"),)

    question_id: Mapped[UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    skill_id: Mapped[UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(20), default=QuestionSkillRole.primary.value)
    weight: Mapped[float] = mapped_column(Float, default=1.0)

    skill: Mapped[Skill] = relationship(back_populates="question_links")


# --------------------------------------------------------------------------- #
# Erros conceituais (spec §4)
# --------------------------------------------------------------------------- #
class Misconception(UUIDMixin, TimestampMixin, Base):
    """Erro conceitual recorrente. Ex.: MIS-LOG-001 "Negar antecedente e consequente
    da condicional" — padrão incorreto P→Q ⇒ ¬P→¬Q; correção ¬(P→Q) ≡ P ∧ ¬Q."""
    __tablename__ = "misconceptions"

    code: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    wrong_pattern: Mapped[str | None] = mapped_column(Text)   # padrão de raciocínio incorreto
    correction: Mapped[str | None] = mapped_column(Text)      # como corrigir
    skill_id: Mapped[UUID | None] = mapped_column(ForeignKey("skills.id", ondelete="SET NULL"), index=True)


class OptionMisconception(UUIDMixin, Base):
    """Liga uma ALTERNATIVA ERRADA (por índice, casando com `questions.options`) a um
    misconception — permite dizer não só QUE errou, mas provavelmente POR QUÊ (spec §4).
    Não precisa existir para todas as alternativas."""
    __tablename__ = "option_misconceptions"
    __table_args__ = (UniqueConstraint("question_id", "option_index"),)

    question_id: Mapped[UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    option_index: Mapped[int] = mapped_column(Integer)  # mesmo índice de correct_option/options
    misconception_id: Mapped[UUID] = mapped_column(ForeignKey("misconceptions.id", ondelete="CASCADE"))
    explanation: Mapped[str | None] = mapped_column(Text)  # diagnóstico específico da alternativa

    misconception: Mapped[Misconception] = relationship()


# --------------------------------------------------------------------------- #
# Transferência (spec §5/§9)
# --------------------------------------------------------------------------- #
class QuestionFamily(UUIDMixin, TimestampMixin, Base):
    """Agrupa questões do MESMO princípio (não necessariamente enunciado parecido),
    para selecionar uma questão diferente e testar transferência.
    Ex.: code=NEGACAO_CONDICIONAL_TRANSFER."""
    __tablename__ = "question_families"

    code: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)


# --------------------------------------------------------------------------- #
# Estado do aluno (spec §11)
# --------------------------------------------------------------------------- #
class UserSkillState(UUIDMixin, TimestampMixin, Base):
    """Estimativa do conhecimento do aluno POR HABILIDADE. Separa domínio (mastery_score)
    de memória (memory_stability/retrievability). Alimentada pelo motor adaptativo (F3);
    aqui só o esqueleto de dados. `mastery_score` NÃO é percentual bruto de acertos."""
    __tablename__ = "user_skill_states"
    __table_args__ = (UniqueConstraint("user_id", "skill_id"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    skill_id: Mapped[UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), index=True)

    # Domínio × memória (estimativas do sistema)
    mastery_score: Mapped[float] = mapped_column(Float, default=0.0)
    memory_stability: Mapped[float | None] = mapped_column(Float)
    difficulty_estimate: Mapped[float | None] = mapped_column(Float)
    retrievability: Mapped[float | None] = mapped_column(Float)

    # Linha do tempo
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)

    # Contadores
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    correct_attempts: Mapped[int] = mapped_column(Integer, default=0)
    wrong_attempts: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_successes: Mapped[int] = mapped_column(Integer, default=0)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)

    # Sinais pedagógicos finos
    high_confidence_errors: Mapped[int] = mapped_column(Integer, default=0)   # errado + confiante (spec §44)
    low_confidence_corrects: Mapped[int] = mapped_column(Integer, default=0)  # certo + chute/dúvida (spec §43)
    transfer_successes: Mapped[int] = mapped_column(Integer, default=0)
    last_response_time: Mapped[int | None] = mapped_column(Integer)

    state: Mapped[str] = mapped_column(String(20), default=SkillState.UNSEEN.value, index=True)

    skill: Mapped[Skill] = relationship()


# --------------------------------------------------------------------------- #
# Evento bruto de aprendizagem (spec §34/§35) — append-only, base de recalibração
# --------------------------------------------------------------------------- #
class LearningEvent(UUIDMixin, Base):
    """Log estruturado e IMUTÁVEL de cada evento relevante (resposta, abertura de
    microaula, checkpoint de áudio, submissão de dissertativa…). Guarda o evento BRUTO,
    não só o resultado agregado, para permitir recalibrar o algoritmo depois sem perder
    histórico. Referências nullable de propósito (um evento de UI pode não ter questão)."""
    __tablename__ = "learning_events"

    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[UUID | None] = mapped_column(ForeignKey("questions.id", ondelete="SET NULL"), index=True)
    skill_id: Mapped[UUID | None] = mapped_column(ForeignKey("skills.id", ondelete="SET NULL"), index=True)
    event_type: Mapped[str] = mapped_column(String(40), index=True)

    selected_option: Mapped[int | None] = mapped_column(Integer)
    correct: Mapped[bool | None] = mapped_column(Boolean)
    confidence: Mapped[str | None] = mapped_column(String(20))
    response_time: Mapped[int | None] = mapped_column(Integer)
    hints: Mapped[int | None] = mapped_column(Integer)
    session_id: Mapped[str | None] = mapped_column(String(64), index=True)
    review_interval: Mapped[int | None] = mapped_column(Integer)
    scheduler_state_before: Mapped[dict | None] = mapped_column(JSON)
    scheduler_state_after: Mapped[dict | None] = mapped_column(JSON)
    payload: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now().astimezone(), index=True
    )
