"""Tools de leitura do banco de questões (Fase 1). Toda a regra de negócio vive
em `app.services.question_query`; aqui só abrimos uma sessão de banco, chamamos o
serviço e devolvemos dados serializáveis. Só expõem material PUBLICADO — gabarito
e explicação saem apenas pela tool dedicada `obter_gabarito`."""

from app.db.session import SessionLocal
from app.services import question_query as qq


def register(mcp) -> None:
    @mcp.tool()
    def listar_filtros() -> dict:
        """Lista os valores de filtro disponíveis no banco de questões: bancas,
        matérias e concursos. Use ANTES de `buscar_questoes` para montar filtros
        que realmente retornam resultado (os nomes precisam existir no banco)."""
        with SessionLocal() as db:
            return qq.list_filters(db)

    @mcp.tool()
    def buscar_questoes(
        banca: str | None = None,
        materia: str | None = None,
        assunto: str | None = None,
        concurso: str | None = None,
        ano: int | None = None,
        dificuldade: int | None = None,
        limite: int = 10,
    ) -> list[dict]:
        """Busca questões PUBLICADAS por filtros opcionais, combinados com E (AND).
        Retorna enunciado e alternativas, SEM o gabarito (peça-o à parte com
        `obter_gabarito`, para preservar o modo estudo).

        Args:
            banca: banca examinadora (ex.: "VUNESP", "FCC"); casamento parcial.
            materia: matéria/disciplina (ex.: "Direito Administrativo").
            assunto: tópico específico dentro da matéria (ex.: "Controle Externo").
            concurso: nome do concurso/edital (ex.: "TCE-SP").
            ano: ano de aplicação da prova de origem (ex.: 2025).
            dificuldade: nível de 1 (fácil) a 5 (difícil).
            limite: máximo de questões a retornar (padrão 10, teto 50).

        Returns:
            Lista de questões: id, enunciado, alternativas, banca, ano, matéria,
            assunto e dificuldade. Lista vazia se nada casar com os filtros.
        """
        with SessionLocal() as db:
            rows = qq.search_questions(
                db,
                banca=banca,
                materia=materia,
                assunto=assunto,
                concurso=concurso,
                ano=ano,
                dificuldade=dificuldade,
                limite=limite,
            )
            return [qq.serialize_question_public(q) for q in rows]

    @mcp.tool()
    def obter_gabarito(questao_id: str) -> dict:
        """Retorna o gabarito (alternativa correta) e a explicação de UMA questão
        publicada, identificada pelo `id` vindo de `buscar_questoes`. Separado da
        busca de propósito, para permitir o modo estudo (responder antes de ver).

        Args:
            questao_id: id (UUID) da questão.

        Returns:
            indice_correto (posição 0-based da alternativa correta),
            resposta_correta (texto da alternativa) e explicacao. Se o id não
            existir ou a questão não estiver publicada, retorna {"erro": ...}.
        """
        with SessionLocal() as db:
            res = qq.get_answer_key(db, questao_id)
            if res is None:
                return {"erro": "Questão não encontrada ou não publicada."}
            return res

    @mcp.tool()
    def estatisticas_banco(agrupar_por: str) -> list[dict]:
        """Conta quantas questões PUBLICADAS existem agrupadas por uma dimensão.

        Args:
            agrupar_por: "banca", "materia" ou "ano".

        Returns:
            Lista de {dimensão, questoes}, ordenada da maior contagem para a menor.
            Se `agrupar_por` for inválido, retorna [{"erro": ...}].
        """
        with SessionLocal() as db:
            try:
                return qq.bank_counts(db, agrupar_por)
            except ValueError as exc:
                return [{"erro": str(exc)}]
