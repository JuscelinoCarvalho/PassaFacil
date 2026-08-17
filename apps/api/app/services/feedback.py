"""Montagem do feedback adaptativo de uma questão objetiva (Fase 2 do full remake).

Concentra a lógica pedagógica das seções §7 (feedback adaptativo) e §8 (microaula
em camadas) da spec, DESACOPLADA das rotas/UI. Degrada com elegância: enquanto o
conteúdo novo (misconceptions por alternativa, microaula estruturada) não estiver
autorado, cai no que já existe hoje (explanation + topic.description) — nada quebra.
"""

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Misconception, OptionMisconception, Question

# Vocabulário de confiança (spec §6) — validado aqui para não espalhar pela API.
CONFIDENCE_VALUES = {"chutei", "duvida", "confiante"}


def normalize_confidence(value: str | None) -> str | None:
    """Aceita só os valores conhecidos; qualquer outra coisa vira None (opcional)."""
    if value is None:
        return None
    v = value.strip().lower()
    return v if v in CONFIDENCE_VALUES else None


def _layered_micro_lesson(question: Question) -> dict:
    """Camadas 1/2/3 (spec §8) com fallback gracioso:
    - essential (camada 1): estruturada se autorada; senão None (o front usa a
      explanation, sempre mostrada, como camada 1);
    - deep (camada 2): só se autorada;
    - mastery (camada 3): conteúdo amplo autorado OU, na falta, a descrição do tópico
      (que é o que hoje aparece como "micro-aula")."""
    ml = question.micro_lesson if isinstance(question.micro_lesson, dict) else {}
    topic_desc = question.topic.description if question.topic else None
    return {
        "essential": ml.get("essential"),
        "deep": ml.get("deep"),
        "mastery": ml.get("mastery") or topic_desc,
    }


def build_answer_feedback(db, question: Question, selected_option: int) -> dict:
    """Feedback completo de uma resposta. Não persiste nada (as rotas cuidam disso).

    Retorna: is_correct, correct_option, explanation (por que a correta está certa),
    why_wrong (diagnóstico da alternativa marcada, quando errada e houver material),
    misconception {code,name}, micro_lesson {essential,deep,mastery} e o campo legado
    `micro_aula` (topic.description) para compatibilidade com telas antigas."""
    is_correct = selected_option == question.correct_option
    micro = _layered_micro_lesson(question)
    feedback = {
        "is_correct": is_correct,
        "correct_option": question.correct_option,
        "explanation": question.explanation,
        "why_wrong": None,
        "misconception": None,
        "micro_lesson": micro,
        # Legado: telas ainda não migradas leem `micro_aula` como string.
        "micro_aula": question.topic.description if question.topic else None,
    }
    if is_correct:
        return feedback

    # Diagnóstico específico da alternativa marcada (spec §7): linguagem NÃO acusatória
    # ("Seu raciocínio pode ter seguido..."), nunca "Você pensou...".
    link = db.scalar(
        select(OptionMisconception)
        .where(
            OptionMisconception.question_id == question.id,
            OptionMisconception.option_index == selected_option,
        )
        .options(selectinload(OptionMisconception.misconception))
    )
    if link:
        mis: Misconception | None = link.misconception
        parts: list[str] = []
        if link.explanation:
            parts.append(link.explanation)
        elif mis and mis.wrong_pattern:
            parts.append(f"Seu raciocínio pode ter seguido: {mis.wrong_pattern}")
        if mis and mis.correction:
            parts.append(mis.correction)
        feedback["why_wrong"] = " ".join(parts) or None
        if mis:
            feedback["misconception"] = {"code": mis.code, "name": mis.name}
    return feedback
