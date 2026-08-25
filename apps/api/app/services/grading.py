"""Correção por IA das questões discursivas — cascata de provedores GRATUITOS.

Compara a resposta do aluno com o espelho (resposta-modelo) e a grade de
critérios e devolve a nota final de cada critério + a justificativa. Usa só a
stdlib (urllib), no mesmo estilo de services/asaas.py e services/google_ads.py —
todos os provedores suportados expõem o endpoint compatível com a API OpenAI
(POST /chat/completions), então o código é único: muda apenas base_url, modelo e
chave.

A cascata tenta cada provedor na ordem de `settings.grading_order` e cai para o
próximo quando um falha (rede, limite de uso, resposta inválida). Se todos
falharem — ou se nenhuma chave estiver configurada — devolve None, e o app cai na
autoavaliação manual (Fase 1). Correção nunca deve derrubar o envio da resposta.
"""

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from app.core.config import settings

logger = logging.getLogger("passafacil.grading")

STATUS_VALUES = {"atendido", "parcial", "ausente"}


def _derive_status(nota: float, teto: float) -> str:
    """Status do critério (spec §27) a partir da nota, quando a IA não o informa."""
    if nota <= 0:
        return "ausente"
    if nota >= teto:
        return "atendido"
    return "parcial"


@dataclass
class GradingResult:
    scores: dict[str, float]      # {codigo: nota atribuída}
    feedback: dict[str, str]      # {codigo: justificativa da nota}
    comentario: str               # comentário geral sobre a resposta
    total: float                  # soma das notas (já clampada aos tetos)
    provider: str                 # provedor que efetivamente corrigiu
    # Fase 7 — correção item-a-item (spec §27): {codigo: {nota, status, evidencia, justificativa}}
    items: dict[str, dict] = field(default_factory=dict)


# base_url / model / api_key de cada provedor, resolvidos a partir das settings.
def _provider_conf(name: str) -> tuple[str, str, str] | None:
    """(base_url, model, api_key) do provedor, ou None se não configurado."""
    mapping = {
        "groq": (settings.groq_base_url, settings.groq_model, settings.groq_api_key),
        "gemini": (settings.gemini_base_url, settings.gemini_model, settings.gemini_api_key),
        "openrouter": (settings.openrouter_base_url, settings.openrouter_model, settings.openrouter_api_key),
        "cerebras": (settings.cerebras_base_url, settings.cerebras_model, settings.cerebras_api_key),
    }
    conf = mapping.get(name)
    if not conf:
        return None
    base_url, model, api_key = conf
    if not api_key:
        return None
    return base_url.rstrip("/"), model, api_key


SYSTEM_PROMPT = (
    "Você é um examinador de provas discursivas de concurso público, no padrão da "
    "banca VUNESP. Sua tarefa é corrigir a resposta de um candidato SOMENTE com base "
    "no espelho (resposta-modelo) e na grade de critérios fornecidos.\n\n"
    "Regras de correção:\n"
    "- Avalie cada critério de forma independente e atribua uma nota entre 0 e o "
    "teto do critério.\n"
    "- DÊ CRÉDITO PARCIAL. Se o candidato acertou parte do que o critério exige, a "
    "nota deve refletir isso proporcionalmente (use casas decimais, ex.: 2.5). Não "
    "zere um critério que foi parcialmente contemplado.\n"
    "- Ignore erros de português, ortografia e forma; avalie o CONTEÚDO jurídico/"
    "técnico frente ao espelho.\n"
    "- Reconheça sinônimos e paráfrases: o candidato não precisa usar as mesmas "
    "palavras do espelho, desde que demonstre o conhecimento exigido.\n"
    "- Na justificativa, seja objetivo e didático: diga o que o candidato cobriu e "
    "exatamente o que faltou para a nota cheia.\n"
    "- Para cada critério informe também o STATUS: 'atendido' (nota cheia), 'parcial' "
    "(crédito parcial) ou 'ausente' (nota 0); e a EVIDENCIA: um TRECHO LITERAL, copiado "
    "da resposta do candidato, que sustenta a nota (string vazia se ausente).\n\n"
    "Responda ESTRITAMENTE em JSON válido, sem texto fora do JSON, no formato:\n"
    '{"criterios": [{"codigo": "N1", "nota": 2.5, "status": "parcial", '
    '"evidencia": "trecho literal do candidato", "justificativa": "..."}], '
    '"comentario_geral": "..."}'
)


def _build_user_prompt(case, texto_resposta: str) -> str:
    linhas = [
        f"ENUNCIADO:\n{case.enunciado}\n",
    ]
    if case.texto_apoio:
        linhas.append(f"TEXTO DE APOIO:\n{case.texto_apoio}\n")
    linhas.append(f"ESPELHO (RESPOSTA-MODELO DA BANCA):\n{case.model_answer}\n")
    linhas.append("GRADE DE CRITÉRIOS (pontue cada um de 0 até o teto):")
    for c in case.criteria:
        linhas.append(
            f"- {c.codigo} (até {float(c.pontuacao_maxima):g} pts) — {c.descricao}\n"
            f"  Esperado: {c.conteudo_esperado}"
        )
    linhas.append(f"\nRESPOSTA DO CANDIDATO:\n{texto_resposta}")
    return "\n".join(linhas)


def _call_provider(
    base_url: str, model: str, api_key: str, messages: list[dict], max_tokens: int = 1600
) -> dict:
    """Faz a chamada /chat/completions e devolve o JSON já parseado do modelo.

    `max_tokens` é ajustável: chamadas com saída curta (ex.: enriquecer explicação)
    reservam menos tokens, o que ajuda a caber no limite de tokens-por-minuto (TPM)
    dos provedores grátis. Default 1600 preserva o comportamento das discursivas."""
    body = json.dumps(
        {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            # User-Agent explícito é OBRIGATÓRIO: o WAF (Cloudflare) da Groq — e de
            # outros provedores — bloqueia o "Python-urllib/x.y" padrão com HTTP 403.
            "User-Agent": "PassaFacil/1.0 (+https://passafacil.jussa.com.br)",
            # Cabeçalhos que a OpenRouter usa para atribuição de tráfego.
            "HTTP-Referer": settings.site_url,
            "X-Title": "Passa Facil",
        },
    )
    with urllib.request.urlopen(req, timeout=settings.grading_timeout_seconds) as response:
        envelope = json.loads(response.read().decode("utf-8"))
    content = envelope["choices"][0]["message"]["content"]
    return _parse_content(content)


def _parse_content(content: str) -> dict:
    """Extrai o objeto JSON da resposta do modelo, tolerando cercas ```json."""
    text = content.strip()
    if text.startswith("```"):
        # remove a primeira linha (``` ou ```json) e a cerca final
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]
    text = text.strip()
    # fallback: recorta do primeiro { ao último } caso venha texto ao redor
    if not text.startswith("{"):
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1:
            text = text[start : end + 1]
    return json.loads(text)


def _result_from_payload(payload: dict, case, provider: str) -> GradingResult | None:
    """Valida o JSON do modelo contra a grade real e clampa cada nota ao teto."""
    max_by_code = {c.codigo: float(c.pontuacao_maxima) for c in case.criteria}
    scores: dict[str, float] = {}
    feedback: dict[str, str] = {}
    items: dict[str, dict] = {}
    for item in payload.get("criterios", []):
        codigo = str(item.get("codigo", "")).strip()
        if codigo not in max_by_code:
            continue
        try:
            nota = float(item.get("nota"))
        except (TypeError, ValueError):
            continue
        nota = round(max(0.0, min(nota, max_by_code[codigo])), 2)
        scores[codigo] = nota
        just = str(item.get("justificativa") or "").strip()
        if just:
            feedback[codigo] = just
        status = str(item.get("status", "")).strip().lower()
        if status not in STATUS_VALUES:
            status = _derive_status(nota, max_by_code[codigo])
        items[codigo] = {
            "nota": nota,
            "status": status,
            "evidencia": str(item.get("evidencia") or "").strip(),
            "justificativa": just,
        }
    # Só aceita a correção se cobriu TODOS os critérios da grade — caso contrário,
    # a nota total seria injustamente baixa; cai para o próximo provedor.
    if set(scores) != set(max_by_code):
        return None
    total = round(sum(scores.values()), 2)
    comentario = str(payload.get("comentario_geral", "") or "").strip()
    return GradingResult(
        scores=scores, feedback=feedback, comentario=comentario, total=total,
        provider=provider, items=items,
    )


def grade(case, texto_resposta: str) -> GradingResult | None:
    """Corrige a resposta percorrendo a cascata de provedores. Best-effort:
    devolve None (sem levantar) se a correção por IA estiver indisponível."""
    if not settings.grading_enabled or not case.criteria:
        return None
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_prompt(case, texto_resposta)},
    ]
    for name in settings.grading_provider_order:
        conf = _provider_conf(name)
        if not conf:
            continue
        base_url, model, api_key = conf
        try:
            payload = _call_provider(base_url, model, api_key, messages)
            result = _result_from_payload(payload, case, name)
            if result:
                return result
            logger.warning("Correção via %s retornou grade incompleta; tentando o próximo.", name)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            logger.warning("Provedor de correção %s falhou (rede/limite): %s", name, exc)
        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            logger.warning("Provedor de correção %s devolveu resposta inválida: %s", name, exc)
        except Exception as exc:  # noqa: BLE001 — correção nunca pode derrubar o envio
            logger.warning("Erro inesperado na correção via %s: %s", name, exc)
    return None


# ----- Reescrita ativa (Fase 7, spec §29): recorreção de UM critério -----
CRITERION_SYSTEM = (
    "Você é um examinador de provas discursivas de concurso (padrão VUNESP). Avalie "
    "SOMENTE o critério indicado, comparando o trecho reescrito pelo candidato com o "
    "conteúdo esperado. Dê crédito parcial e ignore erros de forma; avalie o conteúdo. "
    "Responda ESTRITAMENTE em JSON, sem texto ao redor: "
    '{"nota": 0.0, "status": "atendido|parcial|ausente", "evidencia": "trecho literal", '
    '"justificativa": "..."}'
)


def _criterion_prompt(case, criterion, texto: str) -> str:
    return (
        f"ENUNCIADO:\n{case.enunciado}\n\n"
        f"CRITÉRIO {criterion.codigo} (até {float(criterion.pontuacao_maxima):g} pts): "
        f"{criterion.descricao}\n"
        f"CONTEÚDO ESPERADO: {criterion.conteudo_esperado}\n\n"
        f"TRECHO REESCRITO PELO CANDIDATO:\n{texto}\n\n"
        "Avalie APENAS este critério."
    )


def grade_criterion(case, criterion, texto: str) -> dict | None:
    """Recorrige um único critério sobre o trecho reescrito. Devolve
    {nota, status, evidencia, justificativa, provider} ou None se a IA falhar."""
    if not settings.grading_enabled:
        return None
    teto = float(criterion.pontuacao_maxima)
    messages = [
        {"role": "system", "content": CRITERION_SYSTEM},
        {"role": "user", "content": _criterion_prompt(case, criterion, texto)},
    ]
    for name in settings.grading_provider_order:
        conf = _provider_conf(name)
        if not conf:
            continue
        base_url, model, api_key = conf
        try:
            data = _call_provider(base_url, model, api_key, messages)
            nota = round(max(0.0, min(float(data.get("nota")), teto)), 2)
            status = str(data.get("status", "")).strip().lower()
            if status not in STATUS_VALUES:
                status = _derive_status(nota, teto)
            return {
                "nota": nota, "status": status,
                "evidencia": str(data.get("evidencia") or "").strip(),
                "justificativa": str(data.get("justificativa") or "").strip(),
                "provider": name,
            }
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            logger.warning("Recorreção via %s falhou (rede/limite): %s", name, exc)
        except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
            logger.warning("Recorreção via %s devolveu resposta inválida: %s", name, exc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Erro inesperado na recorreção via %s: %s", name, exc)
    return None
