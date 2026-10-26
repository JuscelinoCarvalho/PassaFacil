"""Verificação ponta-a-ponta do servidor MCP via stdio (equivalente ao que o
MCP Inspector / Claude Desktop fazem). Semeia um banco temporário, sobe o
servidor como subprocesso e exercita o handshake + as 4 tools pelo protocolo.

Uso:  python -m mcp_server.scripts_e2e_stdio
"""

import asyncio
import json
import os
import tempfile
from pathlib import Path


def _seed(db_path: str) -> None:
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ.setdefault("JWT_SECRET", "e2e-secret")
    from app.db.base import Base
    from app.db.session import SessionLocal, engine
    from app.models import Exam, Question, QuestionProvenance, Subject, Topic

    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        exam = Exam(slug="tce-sp", name="TCE-SP", organization="TCE-SP", board="VUNESP", is_published=True)
        db.add(exam); db.flush()
        subj = Subject(exam_id=exam.id, slug="dir-adm", name="Direito Administrativo")
        db.add(subj); db.flush()
        topic = Topic(subject_id=subj.id, slug="controle-externo", name="Controle Externo")
        db.add(topic); db.flush()
        q = Question(
            topic_id=topic.id, statement="Sobre o controle externo pelo TCE...",
            options=json.dumps(["A", "B", "C", "D"]), correct_option=2,
            explanation="O TCE exerce o controle externo auxiliando o Legislativo.",
            is_published=True, difficulty=4,
        )
        db.add(q); db.flush()
        db.add(QuestionProvenance(
            question_id=q.id, content_hash="e2e-hash", source_name="Prova TCE-SP 2025",
            board="VUNESP", exam_year=2025, rights_status="authorial",
        ))
        db.commit()


def _data(result):
    """Extrai o dado da tool do CallToolResult, tolerando as duas formas que o
    FastMCP usa (structuredContent com/sem "result", ou texto JSON em content)."""
    sc = result.structuredContent
    if sc is not None:
        return sc.get("result", sc) if isinstance(sc, dict) else sc
    return json.loads(result.content[0].text)


async def _run(db_path: str) -> None:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(
        command="python", args=["-m", "mcp_server.server"],
        env={**os.environ, "DATABASE_URL": f"sqlite:///{db_path}"},
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            info = await session.initialize()
            print(f"✓ initialize → servidor '{info.serverInfo.name}'")

            tools = (await session.list_tools()).tools
            print(f"✓ tools/list → {[t.name for t in tools]}")

            print("✓ listar_filtros →", _data(await session.call_tool("listar_filtros", {})))

            qs = _data(await session.call_tool("buscar_questoes", {"banca": "VUNESP"}))
            print(f"✓ buscar_questoes(banca=VUNESP) → {len(qs)} questão(ões); sem gabarito:",
                  "resposta_correta" not in qs[0])
            qid = qs[0]["id"]

            gab = _data(await session.call_tool("obter_gabarito", {"questao_id": qid}))
            print("✓ obter_gabarito →", gab["resposta_correta"])

            est = _data(await session.call_tool("estatisticas_banco", {"agrupar_por": "banca"}))
            print("✓ estatisticas_banco(banca) →", est)
    print("\nTudo certo: o servidor MCP respondeu pelo transporte stdio.")


def main() -> None:
    tmp = tempfile.mkdtemp()
    db_path = str(Path(tmp) / "e2e.db")
    _seed(db_path)
    asyncio.run(_run(db_path))


if __name__ == "__main__":
    main()
