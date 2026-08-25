"""Enriquece por IA as EXPLICAÇÕES rasas/confusas das questões publicadas.

A IA julga se a explicação já ensina o "porquê" (ver services/explanation_enrich).
Só reescreve as inadequadas; as boas (inclusive as curtas de cálculo) ficam intactas.
NUNCA muda o gabarito. Preserva a explicação original em `original_explanation`.

Resumível: o relatório guarda os ids já processados. Rode em lotes com --limit.
Reflete AO VIVO no banco (a API lê a cada request; sem restart).

Uso (produção, chaves do /etc no ambiente):
    set -a; . /etc/passafacil.env; set +a
    .venv/bin/python -m scripts.enriquecer_explicacoes --limit 40            # aplica
    .venv/bin/python -m scripts.enriquecer_explicacoes --limit 10 --dry-run  # simula
    .venv/bin/python -m scripts.enriquecer_explicacoes --only <uuid> [--dry-run]
"""

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Question
from app.services.explanation_enrich import improve_explanation

REPORT = Path(__file__).resolve().parents[3] / "docs" / "acervo" / "observacoes" / "explicacoes_enriquecidas.json"


def _load() -> dict:
    if REPORT.exists():
        return json.loads(REPORT.read_text(encoding="utf-8"))
    return {"processed": [], "changed": [], "updated_at": None}


def _save(state: dict) -> None:
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=40, help="quantas questões processar nesta rodada")
    ap.add_argument("--delay", type=float, default=1.5, help="segundos entre chamadas BEM-SUCEDIDAS (paceia o TPM)")
    ap.add_argument("--backoff", type=float, default=10.0, help="segundos de espera quando a IA indisponibiliza (429), antes de repetir a MESMA questão")
    ap.add_argument("--retries", type=int, default=6, help="tentativas por questão antes de deixá-la pendente")
    ap.add_argument("--give-up-after", type=int, default=20, help="disjuntor: aborta a rodada após N questões seguidas que esgotaram as tentativas (provedor caiu/cota diária)")
    ap.add_argument("--dry-run", action="store_true", help="não grava no banco; só relata")
    ap.add_argument("--only", default="", help="processa apenas esta questão (uuid), ignora o checkpoint")
    args = ap.parse_args()

    state = _load()
    done = set(state["processed"])
    db = SessionLocal()
    try:
        if args.only:
            import uuid as _uuid
            q = db.get(Question, _uuid.UUID(args.only))
            batch = [q] if q else []
        else:
            rows = db.scalars(
                select(Question).where(Question.is_published.is_(True)).order_by(Question.id)
            ).all()
            pending = [q for q in rows if str(q.id) not in done]
            batch = pending[: args.limit]
            print(f"Total publicadas: {len(rows)} | já processadas: {len(done)} | nesta rodada: {len(batch)}")

        adequadas = melhoradas = indisponivel = 0
        consecutive_giveups = 0
        for i, q in enumerate(batch):
            options = json.loads(q.options)
            # Tenta a MESMA questão até converter; no 429 espera o backoff e repete.
            res = None
            for attempt in range(args.retries):
                res = improve_explanation(q.statement, options, q.correct_option, q.explanation or "")
                if res is not None:
                    break
                if attempt < args.retries - 1:
                    time.sleep(args.backoff)
            if res is None:
                indisponivel += 1
                consecutive_giveups += 1
                if consecutive_giveups >= args.give_up_after:
                    print(f"Disjuntor: {consecutive_giveups} questões seguidas sem IA — abortando a rodada (provedor caiu ou cota diária). Re-rode depois; é resumível.")
                    break
                continue  # NÃO marca processada (tenta depois)
            consecutive_giveups = 0

            if res["adequate"]:
                adequadas += 1
            else:
                melhoradas += 1
                antiga = q.explanation or ""
                nova = res["explicacao"]
                if not args.dry_run:
                    if hasattr(q, "original_explanation") and not q.original_explanation:
                        q.original_explanation = antiga
                    q.explanation = nova
                state["changed"].append({
                    "id": str(q.id),
                    "provider": res["provider"],
                    "enunciado": q.statement[:140],
                    "antes": antiga[:400],
                    "depois": nova[:600],
                    "dry_run": args.dry_run,
                })

            if not args.only:
                state["processed"].append(str(q.id))
            if not args.dry_run:
                db.commit()
            _save(state)
            if args.delay and i < len(batch) - 1:
                time.sleep(args.delay)

        print(f"OK — adequadas (intactas): {adequadas} | MELHORADAS: {melhoradas} | IA indisponível: {indisponivel}")
        print(f"Total melhoradas acumulado: {len(state['changed'])} | relatório: {REPORT}")
        if args.dry_run:
            print("(dry-run: nada foi gravado no banco)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
