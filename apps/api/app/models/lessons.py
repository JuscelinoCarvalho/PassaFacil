"""Aulas e áudio interativo (Fase 6 do full remake, spec §20-§23).

Preserva todo conteúdo existente e adiciona estrutura para dividir aulas em unidades
semânticas (LessonSection), com áudio opcional e checkpoints de recuperação
(RetrievalCheckpoint) que reaproveitam questões já cadastradas. Aula pode apontar para
habilidades (LessonSkill, §23), permitindo "rever explicação" levar ao trecho certo.

Tabelas novas → criadas por create_all (sem migração manual). Referências a `questions`
e `skills` são FKs (bases novas ganham a constraint; em prod as tabelas são novas).
"""

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Lesson(UUIDMixin, TimestampMixin, Base):
    """Uma aula (container). `kind`=audio|text. Dividida em seções semânticas."""
    __tablename__ = "lessons"

    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(20), default="audio")
    subject_id: Mapped[UUID | None] = mapped_column(ForeignKey("subjects.id", ondelete="SET NULL"))
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    sections: Mapped[list["LessonSection"]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan", order_by="LessonSection.order"
    )
    skills: Mapped[list["LessonSkill"]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan"
    )


class LessonSection(UUIDMixin, TimestampMixin, Base):
    """Unidade semântica da aula (spec §20: não quebrar por minutagem arbitrária).
    Guarda o texto/transcrição e, quando houver, o áudio do trecho (§22)."""
    __tablename__ = "lesson_sections"
    __table_args__ = (UniqueConstraint("lesson_id", "order"),)

    lesson_id: Mapped[UUID] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str | None] = mapped_column(Text)          # transcrição/texto
    audio_url: Mapped[str | None] = mapped_column(Text)        # trecho de áudio (opcional)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)

    lesson: Mapped[Lesson] = relationship(back_populates="sections")
    checkpoint: Mapped["RetrievalCheckpoint | None"] = relationship(
        back_populates="section", cascade="all, delete-orphan", uselist=False
    )


class RetrievalCheckpoint(UUIDMixin, Base):
    """Checkpoint após um conceito relevante (spec §21): uma pergunta curta de
    recuperação. Reaproveita uma questão já cadastrada (`question_id`) — a correção
    usa o mesmo motor de feedback adaptativo das questões."""
    __tablename__ = "retrieval_checkpoints"

    section_id: Mapped[UUID] = mapped_column(
        ForeignKey("lesson_sections.id", ondelete="CASCADE"), unique=True, index=True
    )
    question_id: Mapped[UUID | None] = mapped_column(ForeignKey("questions.id", ondelete="SET NULL"))
    prompt: Mapped[str | None] = mapped_column(Text)  # enunciado inline (se não usar question_id)

    section: Mapped[LessonSection] = relationship(back_populates="checkpoint")


class LessonSkill(UUIDMixin, Base):
    """Liga uma aula a habilidades (spec §23): errar a habilidade → 'rever explicação'
    pode levar exatamente a esta aula/trecho."""
    __tablename__ = "lesson_skills"
    __table_args__ = (UniqueConstraint("lesson_id", "skill_id"),)

    lesson_id: Mapped[UUID] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    skill_id: Mapped[UUID] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), index=True)

    lesson: Mapped[Lesson] = relationship(back_populates="skills")
