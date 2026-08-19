from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession, PaidUser
from app.models import DiscursiveCase, DiscursiveSubmission, EssayRewrite
from app.schemas.discursive import DiscursiveSubmitRequest, RewriteRequest, SelfAssessRequest
from app.services import grading

router = APIRouter(prefix="/discursive", tags=["discursive"])


def _num(value) -> float | None:
    return float(value) if value is not None else None


def _correcao(sub: DiscursiveSubmission) -> dict | None:
    """A correção da IA já persistida — None quando a IA não estava disponível
    (o front cai na autoavaliação manual)."""
    if sub.ai_scores is None:
        return None
    return {
        "scores": sub.ai_scores,
        "feedback": sub.ai_feedback or {},
        "items": sub.ai_items or {},          # Fase 7 — status/evidência por critério (§27)
        "comentario": sub.ai_comentario,
        "total": _num(sub.ai_total),
        "provider": sub.ai_provider,
        "nota_estimada": True,                 # spec §28 — nunca "nota oficial"
    }


def _correcao_from_result(result: "grading.GradingResult | None") -> dict | None:
    if result is None:
        return None
    return {
        "scores": result.scores,
        "feedback": result.feedback,
        "items": result.items,
        "comentario": result.comentario,
        "total": result.total,
        "provider": result.provider,
        "nota_estimada": True,
    }


def _case_public(case: DiscursiveCase) -> dict:
    """Enunciado SEM o espelho (o aluno vê antes de responder)."""
    return {
        "id": case.id,
        "slug": case.slug,
        "tipo": case.tipo,
        "disciplina": case.disciplina,
        "tema": case.tema,
        "enunciado": case.enunciado,
        "texto_apoio": case.texto_apoio,
        "pontuacao_maxima": _num(case.pontuacao_maxima),
        "limite_linhas": case.limite_linhas,
        "banca_referencia": case.banca_referencia,
        "is_demo": case.is_demo,
    }


def _espelho(case: DiscursiveCase) -> dict:
    """Espelho de correção — só é liberado DEPOIS de o aluno enviar a resposta."""
    return {
        "model_answer": case.model_answer,
        "micro_aula": case.micro_aula,
        "pontuacao_maxima": _num(case.pontuacao_maxima),
        "criteria": [
            {
                "codigo": c.codigo,
                "descricao": c.descricao,
                "conteudo_esperado": c.conteudo_esperado,
                "pontuacao_maxima": _num(c.pontuacao_maxima),
            }
            for c in case.criteria
        ],
    }


def _rewrite_out(r: EssayRewrite) -> dict:
    return {
        "id": r.id, "codigo": r.codigo, "texto": r.texto,
        "nota": _num(r.ai_nota), "status": r.ai_status,
        "evidencia": r.ai_evidencia, "justificativa": r.ai_justificativa,
        "created_at": r.created_at,
    }


def _demo_case(db: DbSession) -> DiscursiveCase | None:
    """O caso marcado como is_demo — usado no test-drive público (sem login)."""
    return db.scalar(
        select(DiscursiveCase)
        .where(DiscursiveCase.is_demo.is_(True), DiscursiveCase.is_published.is_(True))
        .options(selectinload(DiscursiveCase.criteria))
        .order_by(DiscursiveCase.display_order)
    )


@router.get("/demo")
def demo_case(db: DbSession):
    """Enunciado do caso de DEMONSTRAÇÃO — público, para o teste grátis (sem espelho)."""
    case = _demo_case(db)
    if not case:
        raise HTTPException(status_code=404, detail="Nenhum exemplo disponível")
    return _case_public(case)


@router.post("/demo/submit")
def demo_submit(payload: DiscursiveSubmitRequest, db: DbSession):
    """Revela o espelho do caso de demonstração e já devolve a correção da IA.
    NÃO persiste (visitante anônimo); o test-drive é só no navegador."""
    case = _demo_case(db)
    if not case:
        raise HTTPException(status_code=404, detail="Nenhum exemplo disponível")
    result = grading.grade(case, payload.texto_resposta.strip())
    return {"espelho": _espelho(case), "correcao": _correcao_from_result(result)}


@router.get("/cases")
def list_cases(user: PaidUser, db: DbSession):
    cases = db.scalars(
        select(DiscursiveCase)
        .where(DiscursiveCase.is_published.is_(True))
        .order_by(DiscursiveCase.is_demo, DiscursiveCase.display_order, DiscursiveCase.tema)
    ).all()
    return [
        {
            "id": c.id,
            "slug": c.slug,
            "tipo": c.tipo,
            "disciplina": c.disciplina,
            "tema": c.tema,
            "pontuacao_maxima": _num(c.pontuacao_maxima),
            "limite_linhas": c.limite_linhas,
            "is_demo": c.is_demo,
        }
        for c in cases
    ]


@router.get("/cases/{case_id}")
def get_case(case_id: UUID, user: PaidUser, db: DbSession):
    case = db.get(DiscursiveCase, case_id)
    if not case or not case.is_published:
        raise HTTPException(status_code=404, detail="Estudo de caso não encontrado")
    return _case_public(case)


@router.post("/cases/{case_id}/submit")
def submit(case_id: UUID, payload: DiscursiveSubmitRequest, user: PaidUser, db: DbSession):
    case = db.scalar(
        select(DiscursiveCase)
        .where(DiscursiveCase.id == case_id, DiscursiveCase.is_published.is_(True))
        .options(selectinload(DiscursiveCase.criteria))
    )
    if not case:
        raise HTTPException(status_code=404, detail="Estudo de caso não encontrado")
    submission = DiscursiveSubmission(
        user_id=user.id, case_id=case.id, texto_resposta=payload.texto_resposta.strip()
    )
    # Correção automática por IA (best-effort — se indisponível, cai na
    # autoavaliação manual e ai_scores fica None).
    result = grading.grade(case, submission.texto_resposta)
    if result:
        submission.ai_scores = result.scores
        submission.ai_total = result.total
        submission.ai_feedback = result.feedback
        submission.ai_comentario = result.comentario
        submission.ai_provider = result.provider
        submission.ai_items = result.items
    db.add(submission)
    db.commit()
    db.refresh(submission)
    # A revelação do espelho + a correção acontecem aqui — só depois de responder.
    return {
        "submission_id": submission.id,
        "espelho": _espelho(case),
        "correcao": _correcao(submission),
    }


@router.get("/submissions/{submission_id}")
def get_submission(submission_id: UUID, user: PaidUser, db: DbSession):
    submission = db.scalar(
        select(DiscursiveSubmission)
        .where(DiscursiveSubmission.id == submission_id, DiscursiveSubmission.user_id == user.id)
        .options(
            selectinload(DiscursiveSubmission.case).selectinload(DiscursiveCase.criteria),
            selectinload(DiscursiveSubmission.rewrites),
        )
    )
    if not submission:
        raise HTTPException(status_code=404, detail="Envio não encontrado")
    return {
        "submission_id": submission.id,
        "texto_resposta": submission.texto_resposta,
        "self_scores": submission.self_scores,
        "self_total": _num(submission.self_total),
        "correcao": _correcao(submission),
        "case": _case_public(submission.case),
        "espelho": _espelho(submission.case),
        "rewrites": [_rewrite_out(r) for r in submission.rewrites],
    }


@router.patch("/submissions/{submission_id}")
def self_assess(submission_id: UUID, payload: SelfAssessRequest, user: PaidUser, db: DbSession):
    submission = db.scalar(
        select(DiscursiveSubmission)
        .where(DiscursiveSubmission.id == submission_id, DiscursiveSubmission.user_id == user.id)
        .options(selectinload(DiscursiveSubmission.case).selectinload(DiscursiveCase.criteria))
    )
    if not submission:
        raise HTTPException(status_code=404, detail="Envio não encontrado")
    # Clampa cada nota ao teto do critério; ignora códigos inexistentes.
    max_by_code = {c.codigo: float(c.pontuacao_maxima) for c in submission.case.criteria}
    clean: dict[str, float] = {}
    total = 0.0
    for codigo, pts in payload.scores.items():
        if codigo not in max_by_code:
            continue
        value = max(0.0, min(float(pts), max_by_code[codigo]))
        clean[codigo] = value
        total += value
    submission.self_scores = clean
    submission.self_total = round(total, 2)
    db.commit()
    return {"self_total": round(total, 2), "pontuacao_maxima": _num(submission.case.pontuacao_maxima)}


@router.post("/submissions/{submission_id}/rewrite")
def rewrite(submission_id: UUID, payload: RewriteRequest, user: PaidUser, db: DbSession):
    """Reescrita ativa (spec §29): o aluno reescreve o trecho de um critério insuficiente
    e a IA recorrige AQUELE critério. Devolve antes/depois para comparar a evolução (§30)."""
    submission = db.scalar(
        select(DiscursiveSubmission)
        .where(DiscursiveSubmission.id == submission_id, DiscursiveSubmission.user_id == user.id)
        .options(selectinload(DiscursiveSubmission.case).selectinload(DiscursiveCase.criteria))
    )
    if not submission:
        raise HTTPException(status_code=404, detail="Envio não encontrado")
    criterion = next((c for c in submission.case.criteria if c.codigo == payload.codigo), None)
    if not criterion:
        raise HTTPException(status_code=422, detail="Critério inválido")
    graded = grading.grade_criterion(submission.case, criterion, payload.texto.strip())
    if graded is None:
        raise HTTPException(status_code=503, detail="Correção por IA indisponível agora. Tente novamente em instantes.")
    rw = EssayRewrite(
        submission_id=submission.id, codigo=payload.codigo, texto=payload.texto.strip(),
        ai_nota=graded["nota"], ai_status=graded["status"],
        ai_evidencia=graded["evidencia"], ai_justificativa=graded["justificativa"],
        ai_provider=graded["provider"],
    )
    db.add(rw)
    db.commit()
    db.refresh(rw)
    return {
        "codigo": payload.codigo,
        "antes": (submission.ai_items or {}).get(payload.codigo),  # item da 1ª correção (§30)
        "depois": {
            "nota": graded["nota"], "status": graded["status"],
            "evidencia": graded["evidencia"], "justificativa": graded["justificativa"],
        },
        "pontuacao_maxima": _num(criterion.pontuacao_maxima),
        "nota_estimada": True,
    }


@router.get("/me/history")
def history(user: PaidUser, db: DbSession):
    rows = db.scalars(
        select(DiscursiveSubmission)
        .where(DiscursiveSubmission.user_id == user.id)
        .options(selectinload(DiscursiveSubmission.case))
        .order_by(DiscursiveSubmission.created_at.desc())
    ).all()
    return [
        {
            "submission_id": s.id,
            "case_id": s.case_id,
            "tema": s.case.tema,
            "disciplina": s.case.disciplina,
            "self_total": _num(s.self_total),
            "ai_total": _num(s.ai_total),
            # Nota que vale para o histórico: a da IA quando houve correção,
            # senão a autoavaliação manual.
            "total": _num(s.ai_total) if s.ai_total is not None else _num(s.self_total),
            "corrigido_por": "ia" if s.ai_total is not None else ("autoavaliacao" if s.self_total is not None else None),
            "pontuacao_maxima": _num(s.case.pontuacao_maxima),
            "created_at": s.created_at,
        }
        for s in rows
    ]
