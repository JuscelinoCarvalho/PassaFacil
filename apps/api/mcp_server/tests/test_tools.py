"""Testes da Fase 1 do servidor MCP.

Dois níveis:
- `app.services.question_query` — a regra de negócio que as tools expõem verbatim;
- as tools via `mcp.call_tool(...)` — garante que o pipeline MCP (schema + execução)
  está de pé e devolve o que o serviço produz.
"""

import asyncio
import json

import pytest
from sqlalchemy import func, select

from app.db.session import SessionLocal
from app.models import Question
from app.services import question_query as qq
from mcp_server.server import mcp


# --------------------------------------------------------------------------- #
# Serviço compartilhado                                                         #
# --------------------------------------------------------------------------- #

def test_list_filters_only_published(seeded):
    with SessionLocal() as db:
        filtros = qq.list_filters(db)
    assert set(filtros["bancas"]) == {"VUNESP", "FCC"}
    assert set(filtros["materias"]) == {"Direito Administrativo", "Português"}
    assert filtros["concursos"] == ["TCE-SP"]


def test_search_excludes_unpublished_and_owner_only(seeded):
    with SessionLocal() as db:
        rows = qq.search_questions(db, limite=50)
        ids = {str(q.id) for q in rows}
    assert ids == {seeded["q_pub_id"], seeded["q_pub2_id"]}
    assert seeded["q_unpub_id"] not in ids
    assert seeded["q_owner_id"] not in ids


@pytest.mark.parametrize(
    "kwargs,expected",
    [
        ({"banca": "FCC"}, "q_pub2_id"),
        ({"banca": "vunesp"}, "q_pub_id"),          # case-insensitive, parcial
        ({"materia": "Administrativo"}, "q_pub_id"),
        ({"assunto": "Controle"}, "q_pub_id"),
        ({"concurso": "TCE"}, None),                 # casa os dois do TCE-SP
        ({"ano": 2025}, "q_pub_id"),
        ({"ano": 2023}, "q_pub2_id"),
        ({"dificuldade": 4}, "q_pub_id"),
        ({"dificuldade": 2}, "q_pub2_id"),
    ],
)
def test_search_filters(seeded, kwargs, expected):
    with SessionLocal() as db:
        ids = [str(q.id) for q in qq.search_questions(db, **kwargs)]
    if expected is None:
        assert set(ids) == {seeded["q_pub_id"], seeded["q_pub2_id"]}
    else:
        assert ids == [seeded[expected]]


def test_search_limit_is_capped(seeded):
    with SessionLocal() as db:
        assert len(qq.search_questions(db, limite=999)) == 2   # só há 2 publicadas
        assert len(qq.search_questions(db, limite=1)) == 1     # respeita o pedido


def test_serialize_has_no_answer(seeded):
    with SessionLocal() as db:
        q = qq.search_questions(db, banca="VUNESP")[0]
        data = qq.serialize_question_public(q)
    assert data["banca"] == "VUNESP"
    assert data["ano"] == 2025
    assert data["materia"] == "Direito Administrativo"
    assert isinstance(data["alternativas"], list)
    # gabarito/explicação NUNCA vêm na busca
    for leaked in ("resposta_correta", "indice_correto", "correct_option", "explicacao"):
        assert leaked not in data


def test_get_answer_key(seeded):
    with SessionLocal() as db:
        gab = qq.get_answer_key(db, seeded["q_pub_id"])
    assert gab["indice_correto"] == seeded["q_pub_correct"]
    assert gab["resposta_correta"] == "Alt C"
    assert gab["explicacao"]


def test_get_answer_key_blocks_unpublished_and_bad_id(seeded):
    with SessionLocal() as db:
        assert qq.get_answer_key(db, seeded["q_unpub_id"]) is None
        assert qq.get_answer_key(db, seeded["q_owner_id"]) is None
        assert qq.get_answer_key(db, "não-é-uuid") is None


def test_bank_counts(seeded):
    with SessionLocal() as db:
        por_banca = {d["banca"]: d["questoes"] for d in qq.bank_counts(db, "banca")}
        por_ano = {d["ano"]: d["questoes"] for d in qq.bank_counts(db, "ano")}
    assert por_banca == {"VUNESP": 1, "FCC": 1}
    assert por_ano == {2025: 1, 2023: 1}
    with SessionLocal() as db, pytest.raises(ValueError):
        qq.bank_counts(db, "inválido")


def test_public_vs_study_filter_distinction(seeded):
    """owner_only NÃO aparece no público (MCP) mas aparece no fluxo de estudo."""
    with SessionLocal() as db:
        public = db.scalar(select(func.count()).select_from(Question).where(qq.public_filter()))
        study = db.scalar(select(func.count()).select_from(Question).where(qq.published_filter()))
    assert public == 2   # q_pub + q_pub2
    assert study == 3     # + q_owner (owner_only)


# --------------------------------------------------------------------------- #
# Tools via o pipeline MCP                                                       #
# --------------------------------------------------------------------------- #

def _payload(result):
    """Normaliza o retorno de FastMCP.call_tool para o dado estruturado da tool."""
    if isinstance(result, tuple):
        result = result[1] if len(result) > 1 else result[0]
    if isinstance(result, dict):
        # FastMCP embrulha retorno de lista em {"result": [...]}
        return result.get("result", result)
    # sequência de ContentBlocks → texto JSON
    return json.loads(result[0].text)


def _call(name, args):
    return _payload(asyncio.run(mcp.call_tool(name, args)))


def test_tool_listar_filtros(seeded):
    out = _call("listar_filtros", {})
    assert set(out["bancas"]) == {"VUNESP", "FCC"}


def test_tool_buscar_questoes(seeded):
    out = _call("buscar_questoes", {"banca": "FCC"})
    assert len(out) == 1
    assert out[0]["id"] == seeded["q_pub2_id"]
    assert "resposta_correta" not in out[0]


def test_tool_obter_gabarito(seeded):
    out = _call("obter_gabarito", {"questao_id": seeded["q_pub_id"]})
    assert out["resposta_correta"] == "Alt C"
    miss = _call("obter_gabarito", {"questao_id": seeded["q_unpub_id"]})
    assert "erro" in miss


def test_tool_estatisticas_banco(seeded):
    out = _call("estatisticas_banco", {"agrupar_por": "ano"})
    anos = {d["ano"]: d["questoes"] for d in out}
    assert anos == {2025: 1, 2023: 1}
