import enum
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import (
    JSON, Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class SubscriptionPlan(str, enum.Enum):
    free = "free"
    plus = "plus"
    pro = "pro"


class SubscriptionStatus(str, enum.Enum):
    trialing = "trialing"
    active = "active"
    past_due = "past_due"
    canceled = "canceled"


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    password_hash: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    subscription: Mapped["Subscription | None"] = relationship(back_populates="user", uselist=False)
    attempts: Mapped[list["Attempt"]] = relationship(back_populates="user")
    study_tasks: Mapped[list["StudyTask"]] = relationship(back_populates="user")


class Subscription(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "subscriptions"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    plan: Mapped[SubscriptionPlan] = mapped_column(Enum(SubscriptionPlan), default=SubscriptionPlan.free)
    status: Mapped[SubscriptionStatus] = mapped_column(
        Enum(SubscriptionStatus), default=SubscriptionStatus.active
    )
    provider: Mapped[str | None] = mapped_column(String(40))
    provider_customer_id: Mapped[str | None] = mapped_column(String(120), unique=True)
    provider_subscription_id: Mapped[str | None] = mapped_column(String(120), unique=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Conversão Google Ads: marcada ao liberar acesso por pagamento real; o front
    # dispara o gtag na próxima visita e chama /billing/conversion/reported para
    # limpar (garante que a conversão não se perca se a aba fechar durante o Pix).
    conversion_pending: Mapped[bool] = mapped_column(Boolean, default=False)
    conversion_reported: Mapped[bool] = mapped_column(Boolean, default=False)
    # gclid do Google Ads capturado no primeiro acesso (query ?gclid=). Permite a
    # conversão server-side via Google Ads API: não depende do comprador voltar ao
    # site nem sofre com bloqueadores de script. conversion_uploaded = enviada com
    # sucesso pela API; conversion_upload_error guarda a última falha (diagnóstico).
    gclid: Mapped[str | None] = mapped_column(String(512))
    conversion_uploaded: Mapped[bool] = mapped_column(Boolean, default=False)
    conversion_upload_error: Mapped[str | None] = mapped_column(Text)

    user: Mapped[User] = relationship(back_populates="subscription")


class Exam(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "exams"

    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    organization: Mapped[str] = mapped_column(String(160))
    board: Mapped[str] = mapped_column(String(120))
    exam_date: Mapped[date | None] = mapped_column(Date)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)

    subjects: Mapped[list["Subject"]] = relationship(back_populates="exam", cascade="all, delete-orphan")


class Subject(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "subjects"
    __table_args__ = (UniqueConstraint("exam_id", "slug"),)

    exam_id: Mapped[UUID] = mapped_column(ForeignKey("exams.id", ondelete="CASCADE"))
    slug: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(80), default="specific")
    weight: Mapped[int] = mapped_column(Integer, default=1)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    # Especialidade do concurso a que a matéria pertence (ti, atuariais, contabeis,
    # economicas, direito, engenharia-civil). NULL = Conhecimentos Gerais (comum a todas).
    specialty: Mapped[str | None] = mapped_column(String(40), index=True)

    exam: Mapped[Exam] = relationship(back_populates="subjects")
    topics: Mapped[list["Topic"]] = relationship(back_populates="subject", cascade="all, delete-orphan")


class Topic(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "topics"
    __table_args__ = (UniqueConstraint("subject_id", "slug"),)

    subject_id: Mapped[UUID] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"))
    slug: Mapped[str] = mapped_column(String(140))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    difficulty: Mapped[int] = mapped_column(Integer, default=3)

    subject: Mapped[Subject] = relationship(back_populates="topics")
    questions: Mapped[list["Question"]] = relationship(back_populates="topic")


class Question(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "questions"

    topic_id: Mapped[UUID] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"))
    statement: Mapped[str] = mapped_column(Text)
    options: Mapped[str] = mapped_column(Text, comment="JSON array")
    correct_option: Mapped[int] = mapped_column(Integer)
    explanation: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(160), default="Autoral Passa Fácil")
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)

    # ---- Plataforma adaptativa (Fase 1) — campos AO LADO dos originais ----
    # primary_skill_id espelha a habilidade primária (verdade: question_skills).
    primary_skill_id: Mapped[UUID | None] = mapped_column(ForeignKey("skills.id", ondelete="SET NULL"))
    question_family_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("question_families.id", ondelete="SET NULL")
    )
    difficulty: Mapped[int | None] = mapped_column(Integer)  # 1–5
    question_type: Mapped[str] = mapped_column(String(40), default="multiple_choice")
    review_status: Mapped[str] = mapped_column(String(30), default="legacy")  # spec §10
    content_version: Mapped[int] = mapped_column(Integer, default=1)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[str | None] = mapped_column(String(120))
    # Preservação do conteúdo original (spec §51) — populados só na Fase 8.
    original_explanation: Mapped[str | None] = mapped_column(Text)
    original_micro_lesson: Mapped[str | None] = mapped_column(Text)
    # Microaula em camadas (Fase 2, spec §8): {essential:{titulo,regra,aplicacao,
    # pegadinha,macete}, deep:str, mastery:str}. NULL/ausente → fallback gracioso
    # (camada 1 = explanation; camada 3 = topic.description). Ver services/feedback.py.
    micro_lesson: Mapped[dict | None] = mapped_column(JSON)

    topic: Mapped[Topic] = relationship(back_populates="questions")
    attempts: Mapped[list["Attempt"]] = relationship(back_populates="question")
    provenance: Mapped["QuestionProvenance | None"] = relationship(
        back_populates="question", uselist=False
    )


class QuestionProvenance(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "question_provenance"

    question_id: Mapped[UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), unique=True
    )
    external_key: Mapped[str | None] = mapped_column(String(240), unique=True)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    source_name: Mapped[str] = mapped_column(String(200))
    source_url: Mapped[str | None] = mapped_column(Text)
    organization: Mapped[str | None] = mapped_column(String(180))
    board: Mapped[str | None] = mapped_column(String(120))
    exam_year: Mapped[int | None] = mapped_column(Integer)
    rights_status: Mapped[str] = mapped_column(String(40), default="research_only")
    import_batch: Mapped[str | None] = mapped_column(String(120), index=True)

    question: Mapped[Question] = relationship(back_populates="provenance")


class QuestionImportJob(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "question_import_jobs"

    original_filename: Mapped[str] = mapped_column(String(255))
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True)
    document_type: Mapped[str] = mapped_column(String(30), default="exam")
    source_name: Mapped[str] = mapped_column(String(200))
    source_url: Mapped[str | None] = mapped_column(Text)
    rights_status: Mapped[str] = mapped_column(String(40), default="owner_only")
    status: Mapped[str] = mapped_column(String(30), default="uploaded", index=True)
    page_count: Mapped[int | None] = mapped_column(Integer)
    candidate_count: Mapped[int] = mapped_column(Integer, default=0)
    extracted_text_path: Mapped[str | None] = mapped_column(Text)
    preview_json_path: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)


class QuestionDraft(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "question_drafts"
    __table_args__ = (UniqueConstraint("exam_job_id", "question_number"),)

    exam_job_id: Mapped[UUID] = mapped_column(
        ForeignKey("question_import_jobs.id", ondelete="CASCADE"), index=True
    )
    answer_key_job_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("question_import_jobs.id", ondelete="SET NULL")
    )
    question_number: Mapped[int] = mapped_column(Integer)
    statement: Mapped[str] = mapped_column(Text)
    options: Mapped[str] = mapped_column(Text)
    correct_option: Mapped[int | None] = mapped_column(Integer)
    confidence: Mapped[str] = mapped_column(String(30), default="review")
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    topic_id: Mapped[UUID | None] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"))
    reviewer_note: Mapped[str | None] = mapped_column(Text)


class Attempt(UUIDMixin, Base):
    __tablename__ = "attempts"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), index=True)
    selected_option: Mapped[int] = mapped_column(Integer)
    is_correct: Mapped[bool] = mapped_column(Boolean)
    response_time_seconds: Mapped[int | None] = mapped_column(Integer)
    answered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now().astimezone()
    )
    # ---- Plataforma adaptativa (Fase 1) — enriquecimento do evento de resposta ----
    confidence: Mapped[str | None] = mapped_column(String(20))  # chutei|duvida|confiante (spec §6)
    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    session_id: Mapped[str | None] = mapped_column(String(64))
    skill_id: Mapped[UUID | None] = mapped_column(ForeignKey("skills.id", ondelete="SET NULL"))
    is_transfer: Mapped[bool] = mapped_column(Boolean, default=False)  # questão de transferência (spec §9)

    user: Mapped[User] = relationship(back_populates="attempts")
    question: Mapped[Question] = relationship(back_populates="attempts")


class StudyTask(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "study_tasks"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    topic_id: Mapped[UUID | None] = mapped_column(ForeignKey("topics.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(String(240))
    activity_type: Mapped[str] = mapped_column(String(40), default="theory")
    duration_minutes: Mapped[int] = mapped_column(Integer, default=25)
    scheduled_date: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="study_tasks")
    topic: Mapped[Topic | None] = relationship()


class ReviewItem(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "review_items"
    __table_args__ = (UniqueConstraint("user_id", "question_id"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    due_date: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    interval_days: Mapped[int] = mapped_column(Integer, default=1)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    last_result: Mapped[bool | None] = mapped_column(Boolean)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    question: Mapped[Question] = relationship()


class Simulation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "simulations"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(180), default="Simulado TCE-SP")
    status: Mapped[str] = mapped_column(String(30), default="in_progress")
    duration_minutes: Mapped[int] = mapped_column(Integer, default=240)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now().astimezone())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    answers: Mapped[list["SimulationAnswer"]] = relationship(
        back_populates="simulation", cascade="all, delete-orphan"
    )


class SimulationAnswer(UUIDMixin, Base):
    __tablename__ = "simulation_answers"
    __table_args__ = (UniqueConstraint("simulation_id", "question_id"),)

    simulation_id: Mapped[UUID] = mapped_column(ForeignKey("simulations.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[UUID] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"))
    display_order: Mapped[int] = mapped_column(Integer)
    selected_option: Mapped[int | None] = mapped_column(Integer)
    is_correct: Mapped[bool | None] = mapped_column(Boolean)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    simulation: Mapped[Simulation] = relationship(back_populates="answers")
    question: Mapped[Question] = relationship()


# ===================== P5 — Módulo discursivo / estudo de caso =====================
class DiscursiveCase(UUIDMixin, TimestampMixin, Base):
    """Questão discursiva/estudo de caso padrão VUNESP. Guarda enunciado, o espelho
    (resposta-modelo em prosa), a micro-aula de estrutura/raciocínio e os critérios
    pontuáveis (grade). Modelo compatível com a futura correção por IA (Fase 2)."""
    __tablename__ = "discursive_cases"

    subject_id: Mapped[UUID | None] = mapped_column(ForeignKey("subjects.id", ondelete="SET NULL"))
    slug: Mapped[str] = mapped_column(String(140), unique=True)
    tipo: Mapped[str] = mapped_column(String(20), default="estudo_caso")  # dissertativa|estudo_caso
    disciplina: Mapped[str] = mapped_column(String(120))
    tema: Mapped[str] = mapped_column(String(200))
    enunciado: Mapped[str] = mapped_column(Text)
    texto_apoio: Mapped[str | None] = mapped_column(Text)
    model_answer: Mapped[str] = mapped_column(Text)   # espelho / resposta-modelo (prosa)
    micro_aula: Mapped[str] = mapped_column(Text)     # ensino de estrutura e linha de raciocínio
    pontuacao_maxima: Mapped[float] = mapped_column(Numeric(5, 2), default=20)
    limite_linhas: Mapped[int] = mapped_column(Integer, default=30)
    banca_referencia: Mapped[str] = mapped_column(String(60), default="VUNESP")
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)  # demonstração de método (não é TI)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    criteria: Mapped[list["DiscursiveCriterion"]] = relationship(
        back_populates="case", cascade="all, delete-orphan", order_by="DiscursiveCriterion.ordem"
    )


class DiscursiveCriterion(UUIDMixin, Base):
    """Item da grade de correção (N1, N2...) de um estudo de caso."""
    __tablename__ = "discursive_criteria"
    __table_args__ = (UniqueConstraint("case_id", "codigo"),)

    case_id: Mapped[UUID] = mapped_column(ForeignKey("discursive_cases.id", ondelete="CASCADE"), index=True)
    codigo: Mapped[str] = mapped_column(String(10))       # N1, N2...
    descricao: Mapped[str] = mapped_column(Text)          # o que o candidato precisa demonstrar
    conteudo_esperado: Mapped[str] = mapped_column(Text)  # resposta-modelo do critério
    pontuacao_maxima: Mapped[float] = mapped_column(Numeric(5, 2))
    ordem: Mapped[int] = mapped_column(Integer, default=0)

    case: Mapped[DiscursiveCase] = relationship(back_populates="criteria")


class DiscursiveSubmission(UUIDMixin, TimestampMixin, Base):
    """Resposta do aluno + correção. A correção por IA (Fase 2) preenche os campos
    ai_*; a autoavaliação manual (Fase 1) preenche os self_* e serve de fallback
    quando a IA está indisponível."""
    __tablename__ = "discursive_submissions"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    case_id: Mapped[UUID] = mapped_column(ForeignKey("discursive_cases.id", ondelete="CASCADE"), index=True)
    texto_resposta: Mapped[str] = mapped_column(Text)
    self_scores: Mapped[dict | None] = mapped_column(JSON)   # {codigo: pontos} da autoavaliação
    self_total: Mapped[float | None] = mapped_column(Numeric(5, 2))
    # Correção automática por IA (cascata de provedores gratuitos — services/grading.py)
    ai_scores: Mapped[dict | None] = mapped_column(JSON)     # {codigo: nota} atribuída pela IA
    ai_total: Mapped[float | None] = mapped_column(Numeric(5, 2))
    ai_feedback: Mapped[dict | None] = mapped_column(JSON)   # {codigo: justificativa da nota}
    ai_comentario: Mapped[str | None] = mapped_column(Text)  # comentário geral da correção
    ai_provider: Mapped[str | None] = mapped_column(String(40))  # provedor que corrigiu
    # Fase 7 — correção item-a-item (spec §27): {codigo: {nota, status
    # (atendido/parcial/ausente), evidencia (trecho do candidato), justificativa}}.
    ai_items: Mapped[dict | None] = mapped_column(JSON)

    case: Mapped[DiscursiveCase] = relationship()
    rewrites: Mapped[list["EssayRewrite"]] = relationship(
        back_populates="submission", cascade="all, delete-orphan", order_by="EssayRewrite.created_at"
    )


class EssayRewrite(UUIDMixin, TimestampMixin, Base):
    """Reescrita ativa (spec §29): o aluno reescreve o trecho referente a um critério
    insuficiente e a IA recorrige AQUELE critério, permitindo comparar a evolução (§30).
    Transforma feedback em nova produção do aluno — não substitui o aluno pela IA (§32)."""
    __tablename__ = "essay_rewrites"

    submission_id: Mapped[UUID] = mapped_column(
        ForeignKey("discursive_submissions.id", ondelete="CASCADE"), index=True
    )
    codigo: Mapped[str] = mapped_column(String(10))          # critério reescrito (N1, N2...)
    texto: Mapped[str] = mapped_column(Text)                 # trecho reescrito pelo aluno
    ai_nota: Mapped[float | None] = mapped_column(Numeric(5, 2))
    ai_status: Mapped[str | None] = mapped_column(String(20))   # atendido/parcial/ausente
    ai_evidencia: Mapped[str | None] = mapped_column(Text)
    ai_justificativa: Mapped[str | None] = mapped_column(Text)
    ai_provider: Mapped[str | None] = mapped_column(String(40))

    submission: Mapped[DiscursiveSubmission] = relationship(back_populates="rewrites")


class Feedback(UUIDMixin, TimestampMixin, Base):
    """Mensagem de ajuda/reclamação/sugestão enviada pelo widget 'Fale conosco'.
    Pública (não exige login); grava quem enviou quando há sessão."""
    __tablename__ = "feedback_messages"

    category: Mapped[str] = mapped_column(String(20), default="ajuda", index=True)
    message: Mapped[str] = mapped_column(Text)
    contact_email: Mapped[str | None] = mapped_column(String(320))
    page: Mapped[str | None] = mapped_column(String(255))
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    user_email: Mapped[str | None] = mapped_column(String(320))  # snapshot do e-mail logado
    status: Mapped[str] = mapped_column(String(20), default="new", index=True)


class TrialEvent(UUIDMixin, TimestampMixin, Base):
    """Telemetria ANÔNIMA do teste grátis (test-drive), SEPARADA dos dados de usuário.
    Serve só para medir uso/funil: quantos simulam, até onde vão e o nível do texto
    escrito na dissertativa demo. `anon_id` é um UUID gerado no navegador
    (localStorage) — não identifica pessoa. Append-only; retenção limitada
    (expurgo por idade no startup — LGPD: finalidade + minimização)."""
    __tablename__ = "trial_events"

    anon_id: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(40), index=True)
    payload: Mapped[dict | None] = mapped_column(JSON)
