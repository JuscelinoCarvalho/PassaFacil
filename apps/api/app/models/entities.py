import enum
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
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
