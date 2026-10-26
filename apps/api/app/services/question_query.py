"""Consulta do banco de questões — camada compartilhada pela API HTTP e pelo
servidor MCP (`mcp_server/`). Centraliza a regra de "o que pode aparecer" e os
filtros de busca para que nenhuma das duas interfaces monte SQL por conta própria
nem duplique regra de negócio.

Dois níveis de visibilidade:
- `published_filter()` — usado pelo fluxo de estudo logado (inclui material
  `owner_only`, liberado para o aluno pago dentro da plataforma).
- `public_filter()` — usado pelo MCP: SÓ questões `is_published=True`. Material
  `owner_only` tem direitos restritos ao dono e NUNCA é exposto por uma interface
  externa de IA (ver spec §8 — LGPD/direitos).
"""

import json
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Exam, Question, QuestionProvenance, Subject, Topic

# Teto duro de resultados por chamada (spec §5): o cliente pode pedir menos, nunca mais.
MAX_RESULTS = 50
DEFAULT_RESULTS = 10


def published_filter():
    """Questões visíveis no fluxo de estudo logado: publicadas OU `owner_only`
    (material do próprio dono, liberado para o aluno pago dentro da plataforma)."""
    return or_(
        Question.is_published.is_(True),
        Question.provenance.has(QuestionProvenance.rights_status == "owner_only"),
    )


def public_filter():
    """Questões expostas por interfaces externas (MCP): apenas `is_published=True`.
    Exclui `owner_only` de propósito — direitos restritos ao dono."""
    return Question.is_published.is_(True)


# --------------------------------------------------------------------------- #
# Derivações por questão (banca/ano vêm da procedência; caem para o concurso).  #
# --------------------------------------------------------------------------- #

def _banca_of(q: Question) -> str | None:
    if q.provenance and q.provenance.board:
        return q.provenance.board
    if q.topic and q.topic.subject and q.topic.subject.exam:
        return q.topic.subject.exam.board
    return None


def _ano_of(q: Question) -> int | None:
    return q.provenance.exam_year if q.provenance else None


def _load_opts():
    """Eager-load da cadeia Topic→Subject→Exam e da procedência, para serializar
    sem N+1 e sem acessar relação fora da sessão."""
    return (
        selectinload(Question.topic).selectinload(Topic.subject).selectinload(Subject.exam),
        selectinload(Question.provenance),
    )


def serialize_question_public(q: Question) -> dict:
    """Questão para o cliente MCP, SEM gabarito nem explicação (pedidos à parte
    via `get_answer_key`, para preservar o modo estudo)."""
    return {
        "id": str(q.id),
        "enunciado": q.statement,
        "alternativas": json.loads(q.options),
        "banca": _banca_of(q),
        "ano": _ano_of(q),
        "materia": q.topic.subject.name if q.topic and q.topic.subject else None,
        "assunto": q.topic.name if q.topic else None,
        "dificuldade": q.difficulty,
    }


# --------------------------------------------------------------------------- #
# Busca                                                                         #
# --------------------------------------------------------------------------- #

def search_questions(
    db: Session,
    *,
    banca: str | None = None,
    materia: str | None = None,
    assunto: str | None = None,
    concurso: str | None = None,
    ano: int | None = None,
    dificuldade: int | None = None,
    limite: int = DEFAULT_RESULTS,
) -> list[Question]:
    """Busca questões PUBLICADAS por filtros opcionais (todos combinados com AND).
    Texto é casado por ILIKE parcial e parametrizado (sem SQL por string)."""
    limite = max(1, min(int(limite), MAX_RESULTS))
    conditions = [public_filter()]

    if banca:
        # Casa a banca EFETIVA (a mesma que `_banca_of` exibe e as estatísticas
        # contam): a procedência manda; só cai para a banca do concurso quando a
        # questão não tem banca de procedência.
        conditions.append(
            or_(
                Question.provenance.has(QuestionProvenance.board.ilike(f"%{banca}%")),
                and_(
                    ~Question.provenance.has(QuestionProvenance.board.is_not(None)),
                    Question.topic.has(
                        Topic.subject.has(Subject.exam.has(Exam.board.ilike(f"%{banca}%")))
                    ),
                ),
            )
        )
    if materia:
        conditions.append(
            Question.topic.has(
                Topic.subject.has(
                    or_(Subject.name.ilike(f"%{materia}%"), Subject.slug.ilike(f"%{materia}%"))
                )
            )
        )
    if assunto:
        conditions.append(
            Question.topic.has(
                or_(Topic.name.ilike(f"%{assunto}%"), Topic.slug.ilike(f"%{assunto}%"))
            )
        )
    if concurso:
        conditions.append(
            Question.topic.has(
                Topic.subject.has(
                    Subject.exam.has(
                        or_(Exam.name.ilike(f"%{concurso}%"), Exam.slug.ilike(f"%{concurso}%"))
                    )
                )
            )
        )
    if ano is not None:
        conditions.append(Question.provenance.has(QuestionProvenance.exam_year == int(ano)))
    if dificuldade is not None:
        conditions.append(Question.difficulty == int(dificuldade))

    return list(
        db.scalars(
            select(Question).where(*conditions).options(*_load_opts()).limit(limite)
        ).all()
    )


def get_answer_key(db: Session, question_id: str | UUID) -> dict | None:
    """Gabarito + explicação de uma questão publicada. Separado da busca de
    propósito (modo estudo). Retorna None se não existir ou não estiver publicada."""
    try:
        qid = UUID(str(question_id))
    except (ValueError, TypeError):
        return None
    q = db.scalar(select(Question).where(Question.id == qid, public_filter()))
    if not q:
        return None
    options = json.loads(q.options)
    idx = q.correct_option
    correta = options[idx] if isinstance(idx, int) and 0 <= idx < len(options) else None
    return {
        "questao_id": str(q.id),
        "indice_correto": idx,
        "resposta_correta": correta,
        "explicacao": q.explanation,
    }


# --------------------------------------------------------------------------- #
# Filtros disponíveis e estatísticas (agregam só o que está publicado)          #
# --------------------------------------------------------------------------- #

def _published_questions(db: Session) -> list[Question]:
    return list(db.scalars(select(Question).where(public_filter()).options(*_load_opts())).all())


def list_filters(db: Session) -> dict:
    """Valores de filtro válidos (apenas entre questões publicadas), para o modelo
    montar buscas que retornam resultado: bancas, matérias e concursos."""
    bancas: set[str] = set()
    materias: set[str] = set()
    concursos: set[str] = set()
    for q in _published_questions(db):
        banca = _banca_of(q)
        if banca:
            bancas.add(banca)
        if q.topic and q.topic.subject:
            materias.add(q.topic.subject.name)
            if q.topic.subject.exam:
                concursos.add(q.topic.subject.exam.name)
    return {
        "bancas": sorted(bancas),
        "materias": sorted(materias),
        "concursos": sorted(concursos),
    }


def bank_counts(db: Session, agrupar_por: str) -> list[dict]:
    """Contagem de questões publicadas agrupadas por `banca`, `materia` ou `ano`.
    Agregado em Python para manter a derivação de banca/ano idêntica à da busca."""
    agrupar_por = (agrupar_por or "").strip().lower()
    if agrupar_por not in {"banca", "materia", "ano"}:
        raise ValueError("agrupar_por deve ser 'banca', 'materia' ou 'ano'")

    counts: dict[object, int] = {}
    for q in _published_questions(db):
        if agrupar_por == "banca":
            key = _banca_of(q)
        elif agrupar_por == "materia":
            key = q.topic.subject.name if q.topic and q.topic.subject else None
        else:  # ano
            key = _ano_of(q)
        if key is None:
            key = "(sem informação)"
        counts[key] = counts.get(key, 0) + 1

    # ordena por contagem desc, depois pela chave (estável/legível)
    return [
        {agrupar_por: k, "questoes": v}
        for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], str(kv[0])))
    ]
