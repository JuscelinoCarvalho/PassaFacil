"""Autoria DEMONSTRATIVA da Fase 2 numa questão real (idempotente).

Popula, para a questão da NEGAÇÃO DA CONDICIONAL ("trabalhadora e honesta", mnemônico
MANÉ), o conteúdo adaptativo que o motor de feedback (services/feedback.py) usa:
  - 1 Skill (LOG-PROP-NEG-COND) + vínculo QuestionSkill (primary) + espelho em
    questions.primary_skill_id;
  - 3 Misconceptions ligados às alternativas erradas (B inversa, E recíproca, A "negar
    tudo"); a alternativa C fica SEM misconception de propósito (cobertura parcial);
  - microaula em camadas (essential + deep) em questions.micro_lesson; a camada 3
    (mastery) cai no topic.description já existente.

Serve de REFERÊNCIA de como a autoria (§50 da spec) mapeia no modelo. Idempotente:
dedup por code / (question, option_index) — rodar de novo atualiza, não duplica.

Uso (produção): DATABASE_URL=... .venv/bin/python -m scripts.seed_demo_adaptive
"""

from uuid import UUID

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import (
    Misconception, OptionMisconception, Question, QuestionSkill, Skill,
)

QUESTION_ID = UUID("2e058342-377e-4988-a640-5116f239a1a7")  # negação da condicional (RLM)

SKILL = dict(
    code="LOG-PROP-NEG-COND",
    name="Negação da proposição condicional",
    description="Reconhecer e aplicar ¬(P → Q) ≡ P ∧ ¬Q (mantém o antecedente, nega o consequente).",
    difficulty_base=3.5,
    importance=4,
    exam_relevance=4,
)

# code -> (dados do misconception, índice da alternativa, explicação específica da alternativa)
MISCONCEPTIONS = [
    (dict(code="MIS-LOG-001",
          name="Negar antecedente e consequente (inversa)",
          wrong_pattern="transformar P → Q em ¬P → ¬Q (mantendo o 'se… então')",
          correction="A negação de um condicional não é outro condicional: ¬(P → Q) ≡ P ∧ ¬Q."),
     1,  # alternativa B
     "Seu raciocínio pode ter seguido a inversa: negar o antecedente e o consequente mantendo o 'se… então'."),

    (dict(code="MIS-LOG-002",
          name="Confundir negação com a recíproca",
          wrong_pattern="trocar P → Q pela recíproca Q → P",
          correction="A recíproca não é a negação; a negação é P ∧ ¬Q."),
     4,  # alternativa E
     "Seu raciocínio pode ter seguido a recíproca (Q → P), invertendo a ordem do condicional."),

    (dict(code="MIS-LOG-003",
          name="Negar todas as partes descartando a estrutura",
          wrong_pattern="negar tudo e trocar a conjunção, sem preservar o antecedente",
          correction="Mantenha o antecedente e negue só o consequente: P ∧ ¬Q."),
     0,  # alternativa A
     "Seu raciocínio pode ter negado todas as partes de uma vez, descartando a estrutura do condicional."),
]

MICRO_LESSON = {
    "essential": {
        "titulo": "Negação da condicional",
        "regra": "¬(P → Q) ≡ P ∧ ¬Q — mantém P, troca o 'então' por E, nega Q.",
        "aplicacao": ("P = 'é trabalhadora e honesta'; Q = 'sente-se realizada e olha com admiração'. "
                      "Logo P ∧ ¬Q = 'é trabalhadora e honesta E (não se sente realizada OU não olha com "
                      "admiração)' → alternativa D."),
        "pegadinha": ("Não vire P → Q na inversa ¬P → ¬Q (alt. B) nem na recíproca Q → P (alt. E). "
                      "A negação de um condicional NUNCA é outro condicional."),
        "macete": ("MANÉ (\"Mané\") = MAntém o antecedente e NEga o consequente: P ∧ ¬Q. "
                   "Depois, como Q é uma conjunção, De Morgan nega Q trocando o E por OU."),
    },
    "deep": ("Por que ¬(P → Q) = P ∧ ¬Q? Um condicional só é falso num único caso: P verdadeiro e Q falso. "
             "Negar a afirmação é justamente afirmar esse caso — P ocorre E Q não ocorre. Como Q aqui é uma "
             "conjunção ('realizada E admiração'), por De Morgan ¬Q = 'não realizada OU não admiração' (o E vira OU). "
             "Compare com estruturas parecidas, que NÃO são a negação: contrapositiva ¬Q → ¬P (equivale ao original), "
             "recíproca Q → P e inversa ¬P → ¬Q."),
    # 'mastery' (camada 3) omitido de propósito → cai no topic.description existente.
}


def _upsert(db, model, defaults, **keys):
    """Cria ou atualiza uma linha identificada por `keys`. Retorna (obj, criado?)."""
    obj = db.scalar(select(model).filter_by(**keys))
    created = obj is None
    if created:
        obj = model(**keys, **defaults)
        db.add(obj)
    else:
        for k, v in defaults.items():
            setattr(obj, k, v)
    db.flush()
    return obj, created


def main() -> None:
    db = SessionLocal()
    try:
        question = db.get(Question, QUESTION_ID)
        if not question:
            raise SystemExit(f"Questão {QUESTION_ID} não encontrada neste banco.")

        skill, s_created = _upsert(
            db, Skill,
            {k: v for k, v in SKILL.items() if k != "code"}
            | {"subject_id": question.topic.subject_id, "topic_id": question.topic_id, "status": "active"},
            code=SKILL["code"],
        )
        _upsert(db, QuestionSkill, {"role": "primary", "weight": 1.0},
                question_id=question.id, skill_id=skill.id)
        question.primary_skill_id = skill.id
        question.micro_lesson = MICRO_LESSON
        question.review_status = "approved"

        n_mis = n_link = 0
        for mis_data, option_index, option_expl in MISCONCEPTIONS:
            mis, created = _upsert(
                db, Misconception,
                {k: v for k, v in mis_data.items() if k != "code"} | {"skill_id": skill.id},
                code=mis_data["code"],
            )
            n_mis += int(created)
            _upsert(db, OptionMisconception, {"misconception_id": mis.id, "explanation": option_expl},
                    question_id=question.id, option_index=option_index)
            n_link += 1

        db.commit()
        print(f"OK — skill {'criada' if s_created else 'atualizada'}: {skill.code}")
        print(f"     misconceptions novos: {n_mis} | vínculos de alternativa: {n_link}")
        print(f"     question.primary_skill_id + micro_lesson (camadas) gravados na questão {question.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
