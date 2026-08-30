from app.models.entities import (
    Attempt,
    DiscursiveCase,
    DiscursiveCriterion,
    DiscursiveSubmission,
    EssayRewrite,
    Exam,
    Feedback,
    Question,
    QuestionDraft,
    QuestionImportJob,
    QuestionProvenance,
    ReviewItem,
    Simulation,
    SimulationAnswer,
    StudyTask,
    Subject,
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    Topic,
    TrialEvent,
    User,
)
from app.models.adaptive import (
    Confidence,
    LearningEvent,
    Misconception,
    OptionMisconception,
    QuestionFamily,
    QuestionSkill,
    QuestionSkillRole,
    Skill,
    SkillRelation,
    SkillRelationType,
    SkillState,
    SkillStatus,
    UserSkillState,
)
from app.models.lessons import (
    Lesson,
    LessonSection,
    LessonSkill,
    RetrievalCheckpoint,
)
from app.models.flashcards import (
    FlashCard,
    FlashCardState,
)

__all__ = [
    "Attempt", "DiscursiveCase", "DiscursiveCriterion", "DiscursiveSubmission", "EssayRewrite", "Exam", "Feedback", "Question", "QuestionDraft", "QuestionImportJob", "QuestionProvenance", "ReviewItem", "Simulation", "SimulationAnswer",
    "StudyTask", "Subject", "Subscription", "SubscriptionPlan", "SubscriptionStatus", "Topic", "TrialEvent", "User",
    # Plataforma adaptativa (Fase 1)
    "Skill", "SkillRelation", "QuestionSkill", "Misconception", "OptionMisconception",
    "UserSkillState", "LearningEvent", "QuestionFamily",
    "SkillRelationType", "SkillStatus", "QuestionSkillRole", "SkillState", "Confidence",
    # Aulas e áudio (Fase 6)
    "Lesson", "LessonSection", "RetrievalCheckpoint", "LessonSkill",
    # Discursivas — cartões de recordação ativa (memorização espaçada)
    "FlashCard", "FlashCardState",
]
