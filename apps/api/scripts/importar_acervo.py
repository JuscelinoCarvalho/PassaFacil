"""Importa o acervo de questões gerado a partir das imagens de `novas/`.

Lê os payloads em `docs/acervo/questoes/*.json`, garante que os tópicos existam
(cria sob a matéria correspondente se faltar), deduplica por content_hash /
external_key (mesma lógica do endpoint /question-bank/import) e insere as
questões como `owner_only` e NÃO publicadas (para revisão do dono).

É IDEMPOTENTE: rodar de novo não duplica (o dedup por hash/external_key barra).

Uso (a partir de apps/api, com a venv):
    .venv/bin/python scripts/importar_acervo.py --dry-run   # só relatório
    .venv/bin/python scripts/importar_acervo.py             # aplica no banco

Depois de aplicar: reinicie a API não é necessário (grava direto no Postgres),
mas revise as questões (estão owner_only) antes de publicar.
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from sqlalchemy import select

# Torna 'app' importável quando chamado de apps/api
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models import Exam, Question, QuestionProvenance, Subject, Topic  # noqa: E402

ACERVO = Path(__file__).resolve().parents[3] / "docs" / "acervo" / "questoes"


def content_hash(statement: str, options: list[str]) -> str:
    normalized = re.sub(r"\s+", " ", statement.strip().lower())
    option_text = "|".join(re.sub(r"\s+", " ", item.strip().lower()) for item in options)
    return hashlib.sha256(f"{normalized}|{option_text}".encode("utf-8")).hexdigest()


def run(dry_run: bool) -> None:
    files = sorted(ACERVO.glob("*.json"))
    if not files:
        print(f"Nenhum arquivo em {ACERVO}")
        return

    totals = {"imported": 0, "duplicates": 0, "rejected": 0, "topics_created": 0}
    with SessionLocal() as db:
        for path in files:
            payload = json.loads(path.read_text(encoding="utf-8"))
            exam = db.scalar(select(Exam).where(Exam.slug == payload["exam_slug"]))
            if not exam:
                print(f"[ERRO] exame '{payload['exam_slug']}' não existe — pulei {path.name}")
                continue
            subject = db.scalar(
                select(Subject).where(
                    Subject.exam_id == exam.id, Subject.slug == payload["subject_slug"]
                )
            )
            if not subject:
                print(f"[ERRO] matéria '{payload['subject_slug']}' não existe — pulei {path.name}")
                continue

            # garante tópicos
            for topic_def in payload.get("topics", []):
                topic = db.scalar(
                    select(Topic).where(
                        Topic.subject_id == subject.id, Topic.slug == topic_def["slug"]
                    )
                )
                if not topic:
                    db.add(
                        Topic(
                            subject_id=subject.id,
                            slug=topic_def["slug"],
                            name=topic_def["name"],
                            description=topic_def.get("description"),
                        )
                    )
                    totals["topics_created"] += 1
                    print(f"[+topic] {payload['subject_slug']}/{topic_def['slug']}")
            if not dry_run:
                db.flush()

            topics = {
                t.slug: t
                for t in db.scalars(select(Topic).where(Topic.subject_id == subject.id)).all()
            }

            for q in payload["questions"]:
                if q["correct_option"] >= len(q["options"]):
                    totals["rejected"] += 1
                    print(f"[reject] {q['external_key']}: correct_option fora do range")
                    continue
                topic = topics.get(q["topic_slug"])
                if not topic:
                    totals["rejected"] += 1
                    print(f"[reject] {q['external_key']}: tópico '{q['topic_slug']}' inexistente")
                    continue
                digest = content_hash(q["statement"], q["options"])
                dup = db.scalar(
                    select(QuestionProvenance).where(
                        (QuestionProvenance.content_hash == digest)
                        | (QuestionProvenance.external_key == q.get("external_key"))
                    )
                )
                if dup:
                    totals["duplicates"] += 1
                    print(f"[dup] {q['external_key']} já existe")
                    continue
                totals["imported"] += 1
                print(f"[import] {q['external_key']} -> {payload['subject_slug']}/{q['topic_slug']}")
                if dry_run:
                    continue
                question = Question(
                    topic_id=topic.id,
                    statement=q["statement"].strip(),
                    options=json.dumps([o.strip() for o in q["options"]], ensure_ascii=False),
                    correct_option=q["correct_option"],
                    explanation=q.get("explanation") or "Comentário editorial pendente.",
                    source=payload["source_name"],
                    is_published=False,  # entra para revisão
                )
                db.add(question)
                db.flush()
                db.add(
                    QuestionProvenance(
                        question_id=question.id,
                        external_key=q.get("external_key"),
                        content_hash=digest,
                        source_name=payload["source_name"],
                        organization=payload.get("organization"),
                        board=payload.get("board"),
                        exam_year=payload.get("exam_year"),
                        rights_status=payload.get("rights_status", "owner_only"),
                        import_batch=payload.get("import_batch"),
                    )
                )

        if dry_run:
            db.rollback()
            print("\n[DRY-RUN] nada foi gravado.")
        else:
            db.commit()
            print("\n[OK] gravado no banco.")
    print(f"Resumo: {totals}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Importa o acervo de questões (docs/acervo/questoes).")
    parser.add_argument("--dry-run", action="store_true", help="Só relatório, não grava.")
    run(parser.parse_args().dry_run)
