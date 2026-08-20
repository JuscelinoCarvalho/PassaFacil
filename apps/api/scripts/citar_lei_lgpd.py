#!/usr/bin/env python3
"""Ancora as citações de artigo das questões de LGPD à lei (Lei nº 13.709/2018).

Regra do dono ([[citar-artigo-com-a-lei]]): ao citar um artigo numa explicação,
SEMPRE dizer de qual lei/norma ele é. Muitas questões de LGPD citam "art. 6º",
"art. 18" etc. sem o número/ano da lei. Este script, de forma idempotente e
aditiva, insere " da Lei nº 13.709/2018 (LGPD)" logo após a PRIMEIRA citação de
artigo na explicação — só quando o número da lei ainda não aparece.

Uso:
  python3 scripts/citar_lei_lgpd.py            # dry-run (não grava)
  python3 scripts/citar_lei_lgpd.py --apply    # grava no banco

Requer DATABASE_URL no ambiente (produção): carregue /etc/passafacil.env antes.
"""
import re
import sys

from app.db.session import SessionLocal
from app.models.entities import Question
from sqlalchemy import select

LAW = "Lei nº 13.709/2018"
ANCHOR = f" da {LAW}"
LAW_NUM = "13.709"

# "art. 6º, III"  /  "art. 18"  /  "art. 52"  /  "art. 5º, XIX" ... (para no 1º inciso não-romano).
# Sem \s* antes do º, para NÃO engolir o espaço que segue o número (ex.: "art. 18 assegura").
ART_RE = re.compile(r"art\.\s*\d+\.?º?(?:\s*,\s*[IVXLCDM]+\b)*", re.IGNORECASE)


def is_lgpd(q: Question) -> bool:
    blob = f"{q.statement or ''} {q.explanation or ''}".lower()
    return "lgpd" in blob or "proteção de dados" in blob or "protecao de dados" in blob


def fix_text(text: str) -> str | None:
    """Devolve o texto corrigido, ou None se nada a fazer."""
    if not text or LAW_NUM in text:
        return None
    m = ART_RE.search(text)
    if not m:
        return None
    end = m.end()
    # já vem " da Lei"/" da LGPD" logo depois? então não mexe.
    if re.match(r"\s*d[ao]\s+(lei|lgpd)", text[end:], re.IGNORECASE):
        return None
    return text[:end] + ANCHOR + text[end:]


def main() -> int:
    apply = "--apply" in sys.argv
    db = SessionLocal()
    rows = db.scalars(select(Question)).all()
    changed = 0
    for q in rows:
        if not is_lgpd(q):
            continue
        new_expl = fix_text(q.explanation)
        if new_expl is None:
            continue
        changed += 1
        if changed <= 8 or apply:
            print(f"---- {q.id} (pub={q.is_published})")
            m = ART_RE.search(q.explanation)
            around = q.explanation[max(0, m.start() - 20): m.end() + 60]
            print("  ANTES :", around.replace("\n", " "))
            m2 = ART_RE.search(new_expl)
            around2 = new_expl[max(0, m2.start() - 20): m2.end() + 90]
            print("  DEPOIS:", around2.replace("\n", " "))
        if apply:
            q.explanation = new_expl
    if apply:
        db.commit()
        print(f"\nAPLICADO: {changed} questões de LGPD atualizadas.")
    else:
        print(f"\nDRY-RUN: {changed} questões seriam atualizadas (nada gravado). Rode com --apply para gravar.")
    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
