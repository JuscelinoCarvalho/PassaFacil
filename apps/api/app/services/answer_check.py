"""Verificação por IA do gabarito de questões objetivas — varredura que SINALIZA.

Reaproveita a cascata de provedores de `services/grading.py`. NÃO altera o gabarito:
apenas diz qual alternativa a IA considera correta e com que confiança, para o dono
revisar as divergências. Correção final é sempre humana (spec §10/§52).
"""

import logging

from app.core.config import settings
from app.services.grading import _call_provider, _provider_conf

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Você é um revisor experiente de provas de concurso público (banca VUNESP). "
    "Dada uma questão objetiva e suas alternativas, identifique a ÚNICA alternativa correta. "
    "Responda SOMENTE em JSON válido, sem texto ao redor: "
    '{"letra": "A", "confianca": "alta|media|baixa", "motivo": "justificativa curta"}. '
    "Use confianca 'baixa' quando o enunciado for ambíguo, faltar contexto ou você não tiver certeza."
)


def _user_prompt(statement: str, options: list[str]) -> str:
    linhas = [f"ENUNCIADO:\n{statement}\n", "ALTERNATIVAS:"]
    for i, opt in enumerate(options):
        linhas.append(f"{chr(65 + i)}) {opt}")
    linhas.append("\nQual é a alternativa correta?")
    return "\n".join(linhas)


def verify_answer(statement: str, options: list[str], correct_index: int) -> dict | None:
    """Devolve {suggested_index, letter, confidence, motivo, provider, matches} ou None
    se a IA estiver indisponível. `matches` = a IA concorda com o gabarito cadastrado."""
    if not settings.grading_enabled or not options:
        return None
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _user_prompt(statement, options)},
    ]
    for name in settings.grading_provider_order:
        conf = _provider_conf(name)
        if not conf:
            continue
        base_url, model, api_key = conf
        try:
            data = _call_provider(base_url, model, api_key, messages)  # JSON já parseado
            letra = str(data.get("letra", "")).strip().upper()[:1]
            if not letra:
                continue
            idx = ord(letra) - 65
            if not (0 <= idx < len(options)):
                continue
            return {
                "suggested_index": idx,
                "letter": letra,
                "confidence": str(data.get("confianca", "")).strip().lower(),
                "motivo": (data.get("motivo") or "").strip(),
                "provider": name,
                "matches": idx == correct_index,
            }
        except Exception as exc:  # noqa: BLE001 — varredura best-effort, nunca derruba
            logger.warning("answer_check via %s falhou: %s", name, exc)
    return None
