"""Varredura por IA dos gabaritos das questões publicadas (SINALIZA divergências).

Para cada questão, pergunta à IA qual a alternativa correta e compara com o gabarito
cadastrado. Onde a IA discorda COM CONFIANÇA (alta/media), marca a questão como
`review_status='needs_review'` e grava um relatório. NÃO altera enunciado, alternativas
nem `correct_option` — a correção é sempre humana (spec §10/§52).

Resumível: o próprio relatório guarda os ids já processados. Rode em lotes com --limit.

Uso (produção, com as chaves do /etc no ambiente):
    set -a; . /etc/passafacil.env; set +a
    .venv/bin/python -m scripts.verificar_gabaritos --limit 40
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Question
from app.services.answer_check import verify_answer

REPORT = Path(__file__).resolve().parents[3] / "docs" / "acervo" / "observacoes" / "gabaritos_check.json"


def _load() -> dict:
    if REPORT.exists():
        return json.loads(REPORT.read_text(encoding="utf-8"))
    return {"processed": [], "flags": [], "updated_at": None}


def _save(state: dict) -> None:
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=40, help="quantas questões processar nesta rodada")
    ap.add_argument("--flag-confidences", default="alta,media",
                    help="confianças que marcam needs_review (padrão: alta,media)")
    args = ap.parse_args()
    flag_confs = {c.strip() for c in args.flag_confidences.split(",") if c.strip()}

    state = _load()
    done = set(state["processed"])
    db = SessionLocal()
    try:
        rows = db.scalars(
            select(Question).where(Question.is_published.is_(True)).order_by(Question.id)
        ).all()
        pending = [q for q in rows if str(q.id) not in done]
        batch = pending[: args.limit]
        print(f"Total publicadas: {len(rows)} | já processadas: {len(done)} | nesta rodada: {len(batch)}")

        checked = flagged = unavailable = 0
        for q in batch:
            options = json.loads(q.options)
            res = verify_answer(q.statement, options, q.correct_option)
            if res is None:
                unavailable += 1
                continue  # IA indisponível: NÃO marca como processada (tenta de novo depois)
            checked += 1
            state["processed"].append(str(q.id))
            if not res["matches"] and res["confidence"] in flag_confs:
                flagged += 1
                q.review_status = "needs_review"
                state["flags"].append({
                    "id": str(q.id),
                    "cadastrado": chr(65 + q.correct_option),
                    "ia_sugere": res["letter"],
                    "confianca": res["confidence"],
                    "provider": res["provider"],
                    "motivo": res["motivo"][:300],
                    "enunciado": q.statement[:160],
                })
            db.commit()
            _save(state)
        print(f"OK — verificadas: {checked} | SINALIZADAS (needs_review): {flagged} | IA indisponível: {unavailable}")
        print(f"Total sinalizado acumulado: {len(state['flags'])} | relatório: {REPORT}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
