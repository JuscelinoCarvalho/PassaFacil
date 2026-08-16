#!/usr/bin/env python3
"""Relatório da telemetria ANÔNIMA do teste grátis (tabela trial_events).

Mostra: funil (quantos simulam e até onde vão), quais questões foram acessadas
(e taxa de acerto) e os textos escritos na dissertativa demo (nível dos candidatos).

Uso (dentro de apps/api):
    .venv/bin/python scripts/trial_report.py            # relatório padrão
    .venv/bin/python scripts/trial_report.py --full     # textos completos das dissertativas
    .venv/bin/python scripts/trial_report.py --days 30  # só os últimos 30 dias

Lê o DATABASE_URL do /etc/passafacil.env (parseia; NUNCA usa `source`).
"""
import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, text

ENV_PATH = "/etc/passafacil.env"


def load_database_url() -> str:
    try:
        with open(ENV_PATH) as fh:
            for line in fh:
                line = line.strip()
                if line.startswith("DATABASE_URL="):
                    return line.split("=", 1)[1].strip()
    except FileNotFoundError:
        pass
    sys.exit(f"DATABASE_URL não encontrado em {ENV_PATH}")


def as_dict(payload) -> dict:
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except Exception:
            return {}
    return {}


def bar(pct: float, width: int = 24) -> str:
    filled = round((pct / 100) * width)
    return "█" * filled + "·" * (width - filled)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=None, help="janela em dias (padrão: tudo)")
    ap.add_argument("--full", action="store_true", help="mostra os textos completos das dissertativas")
    args = ap.parse_args()

    engine = create_engine(load_database_url())
    where = ""
    params = {}
    if args.days:
        where = "WHERE created_at >= :cutoff"
        params["cutoff"] = datetime.now(timezone.utc) - timedelta(days=args.days)

    with engine.connect() as c:
        rows = c.execute(
            text(f"SELECT anon_id, event_type, payload, created_at FROM trial_events {where} ORDER BY created_at"),
            params,
        ).all()

    periodo = f"últimos {args.days} dias" if args.days else "todo o período"
    print("\n" + "=" * 60)
    print(f"  TESTE GRÁTIS — telemetria anônima ({periodo})")
    print("=" * 60)

    if not rows:
        print("\n  Ainda sem dados. Nenhum visitante registrado nessa janela.\n")
        return

    STAGES = [
        ("trial_start", "Iniciou o teste"),
        ("question_answered", "Respondeu ≥1 questão"),
        ("results_viewed", "Viu os resultados"),
        ("discursive_opened", "Abriu a dissertativa"),
        ("discursive_submitted", "Escreveu a dissertativa"),
    ]

    visitors = {r.anon_id for r in rows}
    by_type_visitors = defaultdict(set)
    by_type_count = defaultdict(int)
    for r in rows:
        by_type_visitors[r.event_type].add(r.anon_id)
        by_type_count[r.event_type] += 1

    first, last = rows[0].created_at, rows[-1].created_at
    print(f"\n  Visitantes únicos: {len(visitors)}   |   Eventos: {len(rows)}")
    print(f"  De {first:%d/%m/%Y %H:%M} até {last:%d/%m/%Y %H:%M}")

    # ---- FUNIL (visitantes distintos por etapa) ----
    base = len(by_type_visitors.get("trial_start", visitors)) or len(visitors)
    print("\n  FUNIL (visitantes distintos por etapa)")
    print("  " + "-" * 56)
    for key, label in STAGES:
        n = len(by_type_visitors.get(key, set()))
        pct = (n / base * 100) if base else 0
        print(f"  {label:<26} {n:>4}  {bar(pct)} {pct:5.1f}%")

    # ---- QUESTÕES ACESSADAS ----
    q_stats = defaultdict(lambda: {"subject": "?", "total": 0, "correct": 0})
    for r in rows:
        if r.event_type != "question_answered":
            continue
        d = as_dict(r.payload)
        qid = str(d.get("question_id", "?"))
        st = q_stats[qid]
        st["subject"] = d.get("subject", st["subject"])
        st["total"] += 1
        if d.get("correct"):
            st["correct"] += 1

    print("\n  QUESTÕES DA AMOSTRA — acessos e acerto")
    print("  " + "-" * 56)
    if not q_stats:
        print("  (nenhuma questão respondida ainda)")
    else:
        ordered = sorted(q_stats.items(), key=lambda kv: kv[1]["total"], reverse=True)
        print(f"  {'Matéria':<24}{'Vezes':>7}{'Acerto':>9}")
        for _qid, st in ordered:
            acc = (st["correct"] / st["total"] * 100) if st["total"] else 0
            subj = (st["subject"] or "?")[:23]
            print(f"  {subj:<24}{st['total']:>7}{acc:>8.0f}%")

    # ---- DISSERTATIVAS ESCRITAS ----
    subs = [(r.created_at, as_dict(r.payload)) for r in rows if r.event_type == "discursive_submitted"]
    print(f"\n  DISSERTATIVAS ESCRITAS: {len(subs)}")
    print("  " + "-" * 56)
    if subs:
        avg = sum(len(d.get("texto", "") or "") for _t, d in subs) / len(subs)
        print(f"  Tamanho médio: {avg:.0f} caracteres\n")
        for i, (t, d) in enumerate(subs, 1):
            texto = (d.get("texto") or "").strip()
            print(f"  [{i}] {t:%d/%m/%Y %H:%M} · {len(texto)} chars")
            if args.full:
                print("      " + texto.replace("\n", "\n      ") + "\n")
            else:
                snippet = texto[:400].replace("\n", " ")
                print(f"      {snippet}{'…' if len(texto) > 400 else ''}\n")
        if not args.full:
            print("  (use --full para ver os textos completos)")
    print()


if __name__ == "__main__":
    main()
