"""Extrai conteúdo de estudo da transcrição falada do aulão de 10h (resumível, IA).

A transcrição (`novas/aulao_10h.txt`) é fala corrida com timestamps. Este script:
1) limpa (remove os timestamps), 2) quebra em blocos, 3) pede à IA (cascata de
`grading.py`) para extrair, por bloco, questões + pegadinhas + resumos de leis em JSON,
4) grava um arquivo por bloco em `docs/acervo/aulao/chunks/` (resumível).

Depois, `consolidar_aulao.py` (à parte) junta em `docs/acervo/questoes/*` e
`observacoes/` para o import. NÃO inventa: só extrai o que está claro na fala.

Uso (com as chaves do /etc no ambiente):
    set -a; . /etc/passafacil.env; set +a
    .venv/bin/python -m scripts.extrair_aulao --limit 1        # prova de 1 bloco
"""

import argparse
import json
import re
from pathlib import Path

from app.core.config import settings
from app.services.grading import _call_provider, _provider_conf

SRC = Path(__file__).resolve().parents[3] / "novas" / "aulao_10h.txt"
OUT = Path(__file__).resolve().parents[3] / "docs" / "acervo" / "aulao" / "chunks"
WORDS_PER_CHUNK = 900          # ~1.2k tokens de entrada por bloco (cabe no TPM do Groq)

_TS = re.compile(r"^\s*\d+:\d+.*?segundos?", re.IGNORECASE)

SYSTEM_PROMPT = (
    "Você extrai conteúdo de estudo de uma TRANSCRIÇÃO FALADA de uma aula de revisão "
    "para o concurso TCE-SP (banca VUNESP). É fala corrida, com ruído e repetições. "
    "Extraia SOMENTE o que estiver CLARO no trecho; NÃO invente, não complete o que não "
    "foi dito. Responda ESTRITAMENTE em JSON, sem texto ao redor:\n"
    '{"questoes": [{"materia": "...", "enunciado": "...", "alternativas": ["..."], '
    '"gabarito": "A", "comentario": "...", "pegadinha": "..."}], '
    '"pegadinhas": [{"tema": "...", "texto": "..."}], '
    '"leis": [{"norma": "...", "pontos": ["..."]}]}\n'
    "Regras: se as alternativas não forem ditas claramente, deixe a lista vazia. "
    "Se não houver questão/pegadinha/lei no trecho, devolva a lista vazia correspondente. "
    "Prefira registrar PEGADINHAS e PONTOS DE LEI (é o mais valioso da revisão)."
)


def _clean_lines() -> list[str]:
    out = []
    for raw in SRC.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = _TS.sub("", raw).strip()
        if not line or line.lower() == "pesquisar transcrição":
            continue
        out.append(line)
    return out


def _chunks(words: list[str]) -> list[str]:
    return [" ".join(words[i:i + WORDS_PER_CHUNK]) for i in range(0, len(words), WORDS_PER_CHUNK)]


def _extract(text: str) -> dict | None:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"TRECHO DA AULA:\n{text}"},
    ]
    for name in settings.grading_provider_order:
        conf = _provider_conf(name)
        if not conf:
            continue
        base_url, model, api_key = conf
        try:
            data = _call_provider(base_url, model, api_key, messages)
            data["_provider"] = name
            return data
        except Exception as exc:  # noqa: BLE001
            print(f"  extrair via {name} falhou: {exc}")
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="quantos blocos processar (0 = todos os pendentes)")
    ap.add_argument("--dry-run", action="store_true", help="só mostra a limpeza/quantidade de blocos")
    args = ap.parse_args()

    words = " ".join(_clean_lines()).split()
    chunks = _chunks(words)
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"palavras limpas: {len(words)} | blocos (~{WORDS_PER_CHUNK} palavras): {len(chunks)}")
    if args.dry_run:
        print("\n--- amostra do bloco 0 (limpo) ---\n", chunks[0][:900])
        return

    pending = [i for i in range(len(chunks)) if not (OUT / f"{i:04d}.json").exists()]
    todo = pending[: args.limit] if args.limit else pending
    print(f"pendentes: {len(pending)} | processando agora: {len(todo)}")
    q = p = l = 0
    for i in todo:
        res = _extract(chunks[i])
        if res is None:
            print(f"  bloco {i}: IA indisponível — parando (retomável).")
            break
        (OUT / f"{i:04d}.json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
        q += len(res.get("questoes", []) or [])
        p += len(res.get("pegadinhas", []) or [])
        l += len(res.get("leis", []) or [])
        print(f"  bloco {i}: {len(res.get('questoes',[]) or [])}q {len(res.get('pegadinhas',[]) or [])}peg {len(res.get('leis',[]) or [])}leis ({res.get('_provider')})")
    print(f"\nAcumulado nesta rodada — questões: {q} | pegadinhas: {p} | leis: {l}")
    print(f"blocos gravados: {len(list(OUT.glob('*.json')))}/{len(chunks)} em {OUT}")


if __name__ == "__main__":
    main()
