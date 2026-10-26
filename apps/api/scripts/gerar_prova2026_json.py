"""Gera os JSONs do importador (docs/acervo/questoes/) a partir da transcrição
manual em prova2026_data.py, aplicando o GABARITO OFICIAL (GabaritoMarqueX2026.pdf,
Versão 2). Valida: 80 questões, 5 alternativas cada, gabarito presente para todas.

Uso (a partir de apps/api):
    .venv/bin/python scripts/gerar_prova2026_json.py            # gera os JSONs
    .venv/bin/python scripts/gerar_prova2026_json.py --report   # só valida/relata
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pdfplumber

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prova2026_data import QUESTIONS  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
GABARITO_PDF = REPO / "GabaritoMarqueX2026.pdf"
OUT_DIR = REPO / "docs" / "acervo" / "questoes"

EXAM_SLUG = "tce-sp-2026-ti"
SOURCE_NAME = "Prova Objetiva — TCE-SP 2026 (VUNESP) — Auditor de Controle Externo (TI)"
SUBJECT_NAME = {
    "portugues": "Língua Portuguesa", "logica": "Raciocínio Lógico",
    "etica": "Ética Pública e Integridade", "legislacao": "Legislação",
    "seguranca": "Segurança da Informação", "governanca": "Governança e Auditoria de TI",
    "redes": "Redes e Infraestrutura", "banco-dados": "Banco de Dados",
    "engenharia-software": "Engenharia de Software", "desenvolvimento": "Desenvolvimento de Sistemas",
    "lgpd": "LGPD",
}


def load_gabarito() -> dict[int, str]:
    with pdfplumber.open(GABARITO_PDF) as pdf:
        txt = pdf.pages[0].extract_text()
    return {int(a): b for a, b in re.findall(r"(\d+)\s*-\s*([A-E])", txt)}


def validate(gab: dict[int, str]) -> None:
    errs = []
    ns = sorted(q["n"] for q in QUESTIONS)
    if ns != list(range(1, 81)):
        errs.append(f"Esperadas as questões 1..80; vieram {len(ns)} (faltando/duplicadas).")
    for q in QUESTIONS:
        n = q["n"]
        if len(q["options"]) != 5:
            errs.append(f"Q{n}: {len(q['options'])} alternativas (esperado 5).")
        if any(not str(o).strip() for o in q["options"]):
            errs.append(f"Q{n}: alternativa vazia.")
        if n not in gab:
            errs.append(f"Q{n}: sem gabarito oficial.")
        if not q["statement"].strip():
            errs.append(f"Q{n}: enunciado vazio.")
    if errs:
        print("FALHAS DE VALIDAÇÃO:")
        for e in errs:
            print("  -", e)
        raise SystemExit(1)
    print(f"Validação OK: {len(QUESTIONS)} questões, 5 alternativas cada, gabarito completo.")


def build_groups(gab: dict[int, str]) -> dict[str, dict]:
    groups: dict[str, dict] = {}
    for q in QUESTIONS:
        n = q["n"]
        statement = q["statement"]
        if q.get("text"):
            statement = f"{q['text']}\n\n{statement}"
        g = groups.setdefault(q["subject"], {
            "exam_slug": EXAM_SLUG,
            "subject_slug": q["subject"],
            "subject_name": SUBJECT_NAME[q["subject"]],
            "source_name": SOURCE_NAME,
            "organization": "TCE-SP",
            "board": "VUNESP",
            "exam_year": 2026,
            "rights_status": "owner_only",
            "import_batch": "prova-oficial-2026",
            "questions": [],
        })
        g["questions"].append({
            "external_key": f"vun-tcesp-2026-q{n:02d}",
            "topic_slug": q["topic"],
            "statement": statement,
            "options": q["options"],
            "correct_option": "ABCDE".index(gab[n]),
        })
    return groups


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", action="store_true", help="Só valida e relata; não grava.")
    args = ap.parse_args()

    gab = load_gabarito()
    validate(gab)
    groups = build_groups(gab)

    print("Por matéria:")
    for slug, g in sorted(groups.items()):
        print(f"  {slug:22s} {len(g['questions']):>2d}")

    if args.report:
        return
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for slug, g in groups.items():
        path = OUT_DIR / f"prova2026_{slug}.json"
        path.write_text(json.dumps(g, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[gravado] {path.relative_to(REPO)}")


if __name__ == "__main__":
    main()
