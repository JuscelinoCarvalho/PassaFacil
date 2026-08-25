"""Enriquecimento por IA das EXPLICAÇÕES das questões objetivas.

Diferente da varredura de gabaritos (`answer_check`), aqui a IA NÃO decide a
resposta certa (o gabarito cadastrado é a verdade). Ela julga se a EXPLICAÇÃO
atual já ensina *por que* a alternativa correta é correta — e, quando útil, por
que as demais erram / qual a pegadinha. Se já estiver boa, não mexe. Se estiver
rasa, confusa ou só repetir a alternativa, devolve uma versão melhor.

Regras de segurança:
- NUNCA muda a alternativa correta (vai fixa no prompt como gabarito).
- Ao citar artigo, SEMPRE nomear a lei/norma (número) — regra do dono.
- Explicações puramente computacionais boas (PA, chmod, IP...) são consideradas
  ADEQUADAS e ficam intactas — concisão correta não é defeito.

Reaproveita a cascata de provedores de `services/grading.py`. Best-effort:
qualquer falha devolve None (o chamador tenta de novo depois).
"""

import logging

from app.core.config import settings
from app.services.grading import _call_provider, _provider_conf

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Você é professor revisor de questões de concurso (VUNESP). Recebe a questão, o "
    "GABARITO OFICIAL (fixo, NÃO mude) e a explicação atual; avalie e, se preciso, melhore.\n"
    "ADEQUADA = já deixa claro POR QUE a correta é correta (em cálculo, a fórmula/conta basta; não infle). "
    "INADEQUADA = só repete a alternativa, é vaga, confunde conceitos ou omite a distinção cobrada.\n"
    "Se INADEQUADA, reescreva assim: 'Gabarito: <letra>.' + linha em branco + o PORQUÊ conceitual "
    "+ (se útil) linha '⚠️ PEGADINHA: ...' distinguindo os distratores. Regras: não mude o gabarito; "
    "ao citar artigo, nomeie a lei com número (ex.: art. 2º, §1º, da Lei nº 9.609/1998); não invente "
    "número de lei nem fato — na dúvida, explique o conceito geral; português didático e enxuto.\n"
    'Responda SÓ em JSON: {"adequada": true|false, "explicacao": "<só se adequada=false>"}.'
)


def _user_prompt(statement: str, options: list[str], correct_index: int, current: str) -> str:
    linhas = [f"ENUNCIADO:\n{statement}\n", "ALTERNATIVAS:"]
    for i, opt in enumerate(options):
        marca = "  <== GABARITO OFICIAL" if i == correct_index else ""
        linhas.append(f"{chr(65 + i)}) {opt}{marca}")
    linhas.append(f"\nGABARITO OFICIAL: {chr(65 + correct_index)}")
    linhas.append(f"\nEXPLICAÇÃO ATUAL:\n{current or '(vazia)'}")
    linhas.append("\nAvalie e, se necessário, melhore a explicação (sem mudar o gabarito).")
    return "\n".join(linhas)


def improve_explanation(
    statement: str, options: list[str], correct_index: int, current: str
) -> dict | None:
    """Devolve {"adequate": bool, "explicacao": str|None, "provider": str} ou None
    se a IA estiver indisponível. Quando adequate=True, 'explicacao' é None (não mexer)."""
    if not settings.grading_enabled or not options:
        return None
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _user_prompt(statement, options, correct_index, current)},
    ]
    for name in settings.grading_provider_order:
        conf = _provider_conf(name)
        if not conf:
            continue
        base_url, model, api_key = conf
        try:
            # Saída curta (adequada:bool + explicação): 700 tokens bastam e reduzem
            # o consumo de TPM dos provedores grátis (Groq: 8k TPM), acelerando o lote.
            data = _call_provider(base_url, model, api_key, messages, max_tokens=700)
            adequate = bool(data.get("adequada"))
            nova = (data.get("explicacao") or "").strip()
            if not adequate and len(nova) < 40:
                # IA disse "melhorar" mas não entregou texto útil → trata como adequada
                adequate = True
                nova = ""
            return {
                "adequate": adequate,
                "explicacao": None if adequate else nova,
                "provider": name,
            }
        except Exception as exc:  # noqa: BLE001 — best-effort, nunca derruba
            logger.warning("explanation_enrich via %s falhou: %s", name, exc)
    return None
