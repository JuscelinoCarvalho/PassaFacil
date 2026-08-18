"""Aula de áudio DEMO (idempotente) — Fase 6.

Monta uma aula interativa a partir dos 8 áudios-piloto existentes: cada trecho é uma
seção com áudio + transcrição (o enunciado), e um checkpoint que reaproveita a questão
correspondente do teste grátis. Serve de demonstração do modo interativo (spec §21).

Uso (produção): DATABASE_URL=... .venv/bin/python -m scripts.seed_demo_lesson
"""

import re
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Lesson, LessonSection, Question, QuestionProvenance, RetrievalCheckpoint

# Mesma ordem/rótulos do painel de áudio (study.py). n (q{n}) → external_key do trial.
TRIAL_KEYS = [
    "vunesp-tcesp-2025-q02", "vun-2025-adm-q13", "vun-2025-q30", "vun-2025-adm-q17",
    "vun-2025-adm-q20", "pf-ti-bd-13", "pf-ti-gov-05", "vun-2025-adm-q37",
]
TITLES = {
    1: "Língua Portuguesa — interpretação", 2: "Raciocínio Lógico", 3: "Legislação e Ética",
    4: "Segurança da Informação", 5: "Redes e Infraestrutura", 6: "Banco de Dados",
    7: "Governança de TI", 8: "Contratações de TI",
}
PILOT_DIR = Path(__file__).resolve().parents[1] / "media" / "audio_pilot"
LESSON_SLUG = "revisao-audio-gerais-ti"


def main() -> None:
    db = SessionLocal()
    try:
        # external_key → question
        key_to_q = {
            prov.external_key: db.get(Question, prov.question_id)
            for prov in db.scalars(
                select(QuestionProvenance).where(QuestionProvenance.external_key.in_(TRIAL_KEYS))
            ).all()
        }
        files = {int(m.group(1)): p.name for p in PILOT_DIR.glob("q*.mp3")
                 if (m := re.match(r"q(\d+)_", p.name))}

        lesson = db.scalar(select(Lesson).where(Lesson.slug == LESSON_SLUG))
        if not lesson:
            lesson = Lesson(slug=LESSON_SLUG, kind="audio")
            db.add(lesson)
        lesson.title = "Revisão em áudio — Conhecimentos Gerais + TI"
        lesson.description = ("8 trechos curtos em áudio, um por matéria. No modo interativo, "
                              "cada trecho termina num checkpoint para você recuperar o conteúdo.")
        lesson.is_published = True
        lesson.display_order = 0
        db.flush()

        # limpa seções anteriores (idempotente: recria a partir dos pilotos atuais)
        for s in list(lesson.sections):
            db.delete(s)
        db.flush()

        made = 0
        for n in range(1, 9):
            fname = files.get(n)
            if not fname:
                continue
            q = key_to_q.get(TRIAL_KEYS[n - 1])
            section = LessonSection(
                lesson_id=lesson.id, order=n, title=TITLES.get(n, f"Trecho {n}"),
                content=(q.statement if q else None),
                audio_url=f"/api/v1/study/audio-pilot/{fname}",
            )
            db.add(section); db.flush()
            if q:
                db.add(RetrievalCheckpoint(section_id=section.id, question_id=q.id))
            made += 1

        db.commit()
        print(f"OK — aula '{lesson.slug}' com {made} seções (checkpoints reaproveitando questões do trial).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
