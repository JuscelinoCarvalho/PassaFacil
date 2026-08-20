"""F8 — Classifica o acervo em SKILLS (fase 8 do full remake).

Estratégia pragmatica e não-destrutiva: cada TÓPICO vira uma SKILL (a granularidade
dos tópicos já é a habilidade avaliável). Depois, cada QUESTÃO recebe a skill do seu
tópico como habilidade PRIMÁRIA — preenche `questions.primary_skill_id` (espelho) e
cria o vínculo em `question_skills` (verdade). Assim o motor adaptativo, a fila de
revisão e o dashboard "Meu conhecimento" passam a ter massa em toda a base (antes só
a questão-demo tinha skill).

É IDEMPOTENTE: skill deduplicada por `code` (= slug do tópico); questão não recebe
vínculo duplicado. NÃO apaga nada e NÃO altera enunciado/gabarito.

Uso (a partir de apps/api, com a venv e as chaves do /etc no ambiente):
    .venv/bin/python scripts/classificar_skills.py --dry-run   # só relatório
    .venv/bin/python scripts/classificar_skills.py             # aplica no banco
"""
import argparse
import sys
from pathlib import Path

from sqlalchemy import func, select

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models import Question, Subject, Topic  # noqa: E402
from app.models.adaptive import QuestionSkill, Skill  # noqa: E402


def run(dry_run: bool) -> None:
    totals = {"skills_criadas": 0, "skills_existentes": 0, "questoes_ligadas": 0, "ja_ligadas": 0}
    with SessionLocal() as db:
        topics = db.scalars(select(Topic).order_by(Topic.name)).all()
        print(f"tópicos: {len(topics)}")
        for topic in topics:
            skill = db.scalar(select(Skill).where(Skill.code == topic.slug))
            if not skill:
                # dificuldade média das questões do tópico (fallback 3.0)
                avg_diff = db.scalar(
                    select(func.avg(Question.difficulty)).where(
                        Question.topic_id == topic.id, Question.difficulty.isnot(None)
                    )
                )
                skill = Skill(
                    code=topic.slug,
                    name=topic.name,
                    description=topic.description,
                    subject_id=topic.subject_id,
                    topic_id=topic.id,
                    difficulty_base=float(avg_diff) if avg_diff else 3.0,
                )
                totals["skills_criadas"] += 1
                if not dry_run:
                    db.add(skill)
                    db.flush()  # materializa skill.id
            else:
                totals["skills_existentes"] += 1

            # liga as questões do tópico à skill (primária)
            questions = db.scalars(select(Question).where(Question.topic_id == topic.id)).all()
            for q in questions:
                existing = db.scalar(
                    select(QuestionSkill).where(
                        QuestionSkill.question_id == q.id, QuestionSkill.role == "primary"
                    )
                )
                if existing or q.primary_skill_id:
                    totals["ja_ligadas"] += 1
                    continue
                totals["questoes_ligadas"] += 1
                if not dry_run:
                    q.primary_skill_id = skill.id
                    db.add(QuestionSkill(question_id=q.id, skill_id=skill.id, role="primary", weight=1.0))

        if dry_run:
            db.rollback()
            print("\n[DRY-RUN] nada foi gravado.")
        else:
            db.commit()
            print("\n[OK] gravado no banco.")
    print(f"Resumo: {totals}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="F8 — classifica o acervo em skills (tópico→skill).")
    ap.add_argument("--dry-run", action="store_true", help="Só relatório, não grava.")
    run(ap.parse_args().dry_run)
