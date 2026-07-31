import hashlib
import json
import re
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select

from app.api.deps import DbSession, get_owner_user
from app.core.config import settings
from app.models import Question, QuestionDraft, QuestionImportJob, QuestionProvenance, Topic
from app.schemas.question_drafts import AssociateDocuments, DraftBulkAction, DraftUpdate
from app.schemas.question_bank import ImportBatch
from app.services.pdf_questions import extract_pdf_preview

router = APIRouter(prefix="/question-bank", tags=["question-bank"])


def content_hash(statement: str, options: list[str]) -> str:
    normalized = re.sub(r"\s+", " ", statement.strip().lower())
    option_text = "|".join(re.sub(r"\s+", " ", item.strip().lower()) for item in options)
    return hashlib.sha256(f"{normalized}|{option_text}".encode("utf-8")).hexdigest()


@router.get("/stats")
def bank_stats(db: DbSession):
    get_owner_user(db)
    total = db.scalar(select(func.count(Question.id))) or 0
    sourced = db.scalar(select(func.count(QuestionProvenance.id))) or 0
    sources = db.execute(
        select(
            QuestionProvenance.source_name,
            QuestionProvenance.board,
            QuestionProvenance.exam_year,
            QuestionProvenance.rights_status,
            func.count(QuestionProvenance.id),
        ).group_by(
            QuestionProvenance.source_name,
            QuestionProvenance.board,
            QuestionProvenance.exam_year,
            QuestionProvenance.rights_status,
        )
    ).all()
    return {
        "total_questions": total,
        "questions_with_provenance": sourced,
        "sources": [
            {
                "source_name": row[0],
                "board": row[1],
                "exam_year": row[2],
                "rights_status": row[3],
                "questions": row[4],
            }
            for row in sources
        ],
    }


@router.get("/topics")
def list_topics(db: DbSession):
    get_owner_user(db)
    rows = db.scalars(select(Topic).order_by(Topic.name)).all()
    return [{"id": row.id, "slug": row.slug, "name": row.name} for row in rows]


@router.post("/pdf/inspect", status_code=201)
async def inspect_pdf(
    db: DbSession,
    file: UploadFile = File(...),
    document_type: str = Form("exam"),
    source_name: str = Form(...),
    source_url: str | None = Form(None),
    rights_status: str = Form("owner_only"),
):
    get_owner_user(db)
    if document_type not in {"exam", "answer_key"}:
        raise HTTPException(status_code=422, detail="Tipo de documento inválido")
    if rights_status not in {"research_only", "owner_only", "licensed", "public_domain", "authorial"}:
        raise HTTPException(status_code=422, detail="Estado de direitos inválido")
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail="Envie um arquivo PDF")
    content = await file.read()
    if not content.startswith(b"%PDF"):
        raise HTTPException(status_code=415, detail="O arquivo não possui assinatura PDF válida")
    if len(content) > settings.max_pdf_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="PDF excede o limite configurado")

    job_id = uuid4()
    job_dir = Path(settings.question_import_dir).resolve() / str(job_id)
    job_dir.mkdir(parents=True, exist_ok=False)
    pdf_path = job_dir / "source.pdf"
    pdf_path.write_bytes(content)
    job = QuestionImportJob(
        id=job_id,
        original_filename=Path(file.filename).name,
        stored_filename=str(pdf_path),
        document_type=document_type,
        source_name=source_name,
        source_url=source_url,
        rights_status=rights_status,
        status="processing",
    )
    db.add(job)
    db.commit()
    try:
        preview = extract_pdf_preview(pdf_path, job_dir, document_type)
        job.status = "review"
        job.page_count = preview["page_count"]
        job.candidate_count = preview["candidate_count"]
        job.extracted_text_path = preview["text_path"]
        job.preview_json_path = preview["preview_path"]
        db.commit()
        return {
            "id": job.id,
            "status": job.status,
            "filename": job.original_filename,
            "document_type": job.document_type,
            "rights_status": job.rights_status,
            "page_count": job.page_count,
            "candidate_count": job.candidate_count,
            "answer_count": len(preview.get("answers", {})),
            "candidates": preview["candidates"][:100],
            "warnings": preview["warnings"],
        }
    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)[:2000]
        db.commit()
        raise HTTPException(status_code=422, detail="Não foi possível extrair o PDF") from exc


@router.get("/pdf/jobs")
def list_pdf_jobs(db: DbSession):
    get_owner_user(db)
    rows = db.scalars(
        select(QuestionImportJob).order_by(QuestionImportJob.created_at.desc()).limit(50)
    ).all()
    return [
        {
            "id": row.id,
            "filename": row.original_filename,
            "source_name": row.source_name,
            "document_type": row.document_type,
            "rights_status": row.rights_status,
            "status": row.status,
            "page_count": row.page_count,
            "candidate_count": row.candidate_count,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.get("/pdf/jobs/{job_id}")
def pdf_job_preview(job_id: UUID, db: DbSession):
    get_owner_user(db)
    job = db.get(QuestionImportJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Importação não encontrada")
    candidates = []
    warnings = []
    if job.preview_json_path and Path(job.preview_json_path).exists():
        preview = json.loads(Path(job.preview_json_path).read_text(encoding="utf-8"))
        candidates = preview.get("candidates", [])
        warnings = preview.get("warnings", [])
    return {
        "id": job.id,
        "filename": job.original_filename,
        "source_name": job.source_name,
        "status": job.status,
        "page_count": job.page_count,
        "candidate_count": job.candidate_count,
        "candidates": candidates,
        "answers": preview.get("answers", {}) if job.preview_json_path and Path(job.preview_json_path).exists() else {},
        "warnings": warnings,
        "error_message": job.error_message,
    }


@router.post("/pdf/jobs/{job_id}/reprocess")
def reprocess_pdf_job(job_id: UUID, db: DbSession):
    get_owner_user(db)
    job = db.get(QuestionImportJob, job_id)
    if not job or not Path(job.stored_filename).exists():
        raise HTTPException(status_code=404, detail="PDF não encontrado")
    job_dir = Path(job.stored_filename).parent
    preview = extract_pdf_preview(Path(job.stored_filename), job_dir, job.document_type)
    job.status = "review"
    job.page_count = preview["page_count"]
    job.candidate_count = preview["candidate_count"]
    job.extracted_text_path = preview["text_path"]
    job.preview_json_path = preview["preview_path"]
    db.commit()
    return {
        "id": job.id,
        "status": job.status,
        "page_count": job.page_count,
        "candidate_count": job.candidate_count,
        "answer_count": preview["answer_count"],
        "images": sum(1 for item in preview["candidates"] if item.get("image_file")),
    }


@router.get("/pdf/jobs/{job_id}/images/{filename}")
def question_image(job_id: UUID, filename: str, db: DbSession):
    get_owner_user(db)
    job = db.get(QuestionImportJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Importação não encontrada")
    safe_name = Path(filename).name
    image_path = Path(job.stored_filename).parent / "question-images" / safe_name
    if safe_name != filename or not image_path.exists() or image_path.suffix.lower() != ".png":
        raise HTTPException(status_code=404, detail="Imagem não encontrada")
    return FileResponse(image_path, media_type="image/png")


@router.post("/pdf/associate")
def associate_exam_and_key(payload: AssociateDocuments, db: DbSession):
    get_owner_user(db)
    exam = db.get(QuestionImportJob, payload.exam_job_id)
    answer_key = db.get(QuestionImportJob, payload.answer_key_job_id)
    if not exam or exam.document_type != "exam" or exam.status != "review":
        raise HTTPException(status_code=422, detail="Selecione uma prova processada")
    if not answer_key or answer_key.document_type != "answer_key" or answer_key.status != "review":
        raise HTTPException(status_code=422, detail="Selecione um gabarito processado")
    if not exam.preview_json_path or not answer_key.preview_json_path:
        raise HTTPException(status_code=422, detail="Os documentos não possuem prévia")
    exam_preview = json.loads(Path(exam.preview_json_path).read_text(encoding="utf-8"))
    key_preview = json.loads(Path(answer_key.preview_json_path).read_text(encoding="utf-8"))
    answers = key_preview.get("answers", {})
    created = 0
    matched = 0
    missing_key = []
    for candidate in exam_preview.get("candidates", []):
        number = int(candidate["number"])
        correct = answers.get(str(number))
        draft = db.scalar(
            select(QuestionDraft).where(
                QuestionDraft.exam_job_id == exam.id,
                QuestionDraft.question_number == number,
            )
        )
        if not draft:
            draft = QuestionDraft(
                exam_job_id=exam.id,
                answer_key_job_id=answer_key.id,
                question_number=number,
                statement=candidate["statement"],
                options=json.dumps(candidate["options"], ensure_ascii=False),
                correct_option=correct,
                confidence=candidate["confidence"],
            )
            db.add(draft)
            created += 1
        else:
            draft.answer_key_job_id = answer_key.id
            draft.correct_option = correct
        if correct is None:
            missing_key.append(number)
        else:
            matched += 1
    exam.status = "associated"
    answer_key.status = "associated"
    db.commit()
    return {
        "drafts_created": created,
        "matched_answers": matched,
        "missing_answers": missing_key,
        "ready_for_review": matched,
    }


@router.get("/drafts")
def list_drafts(db: DbSession, status: str = "pending", exam_job_id: UUID | None = None):
    get_owner_user(db)
    query = select(QuestionDraft).where(QuestionDraft.status == status)
    if exam_job_id:
        query = query.where(QuestionDraft.exam_job_id == exam_job_id)
    rows = db.scalars(query.order_by(
        QuestionDraft.exam_job_id, QuestionDraft.question_number
    ).limit(500)).all()
    result = []
    preview_cache: dict[UUID, dict] = {}
    for row in rows:
        job = db.get(QuestionImportJob, row.exam_job_id)
        preview = preview_cache.get(row.exam_job_id)
        if preview is None:
            preview = {}
            if job and job.preview_json_path and Path(job.preview_json_path).exists():
                preview = json.loads(Path(job.preview_json_path).read_text(encoding="utf-8"))
            preview_cache[row.exam_job_id] = preview
        candidate = next(
            (item for item in preview.get("candidates", [])
             if int(item["number"]) == row.question_number),
            {},
        )
        result.append({
            "id": row.id,
            "exam_job_id": row.exam_job_id,
            "source_name": job.source_name if job else None,
            "question_number": row.question_number,
            "statement": row.statement,
            "options": json.loads(row.options),
            "correct_option": row.correct_option,
            "confidence": row.confidence,
            "status": row.status,
            "topic_id": row.topic_id,
            "reviewer_note": row.reviewer_note,
            "page_number": candidate.get("page_number"),
            "image_url": (
                f"/api/v1/question-bank/pdf/jobs/{row.exam_job_id}/images/"
                f"{candidate['image_file']}"
                if candidate.get("image_file") else None
            ),
        }
        )
    return result


@router.patch("/drafts/{draft_id}")
def update_draft(draft_id: UUID, payload: DraftUpdate, db: DbSession):
    get_owner_user(db)
    draft = db.get(QuestionDraft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Rascunho não encontrado")
    if len(payload.options) < 2 or any(not item.strip() for item in payload.options):
        raise HTTPException(status_code=422, detail="Informe ao menos duas alternativas")
    if payload.correct_option is not None and not 0 <= payload.correct_option < len(payload.options):
        raise HTTPException(status_code=422, detail="Gabarito fora do intervalo")
    if payload.status not in {"pending", "reviewed", "rejected"}:
        raise HTTPException(status_code=422, detail="Estado de revisão inválido")
    draft.statement = payload.statement.strip()
    draft.options = json.dumps([item.strip() for item in payload.options], ensure_ascii=False)
    draft.correct_option = payload.correct_option
    draft.topic_id = payload.topic_id
    draft.reviewer_note = payload.reviewer_note
    draft.status = payload.status
    db.commit()
    return {"id": draft.id, "status": draft.status}


@router.post("/drafts/bulk")
def bulk_review_drafts(payload: DraftBulkAction, db: DbSession):
    get_owner_user(db)
    if payload.action not in {"review", "reject"}:
        raise HTTPException(status_code=422, detail="Ação em lote inválida")
    drafts = db.scalars(
        select(QuestionDraft).where(QuestionDraft.id.in_(payload.draft_ids))
    ).all()
    changed = 0
    skipped = 0
    for draft in drafts:
        if payload.action == "review":
            if draft.correct_option is None or not (payload.topic_id or draft.topic_id):
                skipped += 1
                continue
            draft.topic_id = payload.topic_id or draft.topic_id
            draft.status = "reviewed"
        else:
            draft.status = "rejected"
        changed += 1
    db.commit()
    return {"changed": changed, "skipped": skipped}


@router.post("/drafts/{draft_id}/publish", status_code=201)
def publish_reviewed_draft(draft_id: UUID, db: DbSession):
    get_owner_user(db)
    draft = db.get(QuestionDraft, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Rascunho não encontrado")
    if draft.status != "reviewed" or draft.topic_id is None or draft.correct_option is None:
        raise HTTPException(
            status_code=422,
            detail="Revise o texto, o tópico e o gabarito antes de adicionar ao banco",
        )
    job = db.get(QuestionImportJob, draft.exam_job_id)
    if not job:
        raise HTTPException(status_code=422, detail="Fonte da questão não encontrada")
    options = json.loads(draft.options)
    digest = content_hash(draft.statement, options)
    if db.scalar(select(QuestionProvenance).where(QuestionProvenance.content_hash == digest)):
        raise HTTPException(status_code=409, detail="Questão já existente no banco")
    can_publish = job.rights_status in {"licensed", "public_domain", "authorial"}
    question = Question(
        topic_id=draft.topic_id,
        statement=draft.statement,
        options=draft.options,
        correct_option=draft.correct_option,
        explanation=draft.reviewer_note or "Comentário editorial pendente.",
        source=job.source_name,
        is_published=can_publish,
    )
    db.add(question)
    db.flush()
    db.add(QuestionProvenance(
        question_id=question.id,
        external_key=f"{draft.exam_job_id}-q{draft.question_number}",
        content_hash=digest,
        source_name=job.source_name,
        source_url=job.source_url,
        organization=None,
        board="VUNESP" if "VUNESP" in job.source_name.upper() else None,
        exam_year=None,
        rights_status=job.rights_status,
        import_batch=str(draft.exam_job_id),
    ))
    draft.status = "published"
    db.commit()
    return {
        "question_id": question.id,
        "status": draft.status,
        "public": can_publish,
        "owner_available": True,
    }


@router.post("/import")
def import_questions(payload: ImportBatch, db: DbSession):
    get_owner_user(db)
    topics = {
        topic.slug: topic for topic in db.scalars(
            select(Topic).where(Topic.slug.in_({item.topic_slug for item in payload.questions}))
        ).all()
    }
    missing_topics = sorted({item.topic_slug for item in payload.questions} - topics.keys())
    if missing_topics:
        raise HTTPException(status_code=422, detail={"unknown_topics": missing_topics})

    imported = 0
    duplicates = 0
    rejected = 0
    can_publish = payload.rights_status in {"licensed", "public_domain", "authorial"}
    for item in payload.questions:
        if item.correct_option >= len(item.options):
            rejected += 1
            continue
        digest = content_hash(item.statement, item.options)
        duplicate = db.scalar(
            select(QuestionProvenance).where(
                (QuestionProvenance.content_hash == digest)
                | (
                    QuestionProvenance.external_key == item.external_key
                    if item.external_key
                    else False
                )
            )
        )
        if duplicate:
            duplicates += 1
            continue
        question = Question(
            topic_id=topics[item.topic_slug].id,
            statement=item.statement.strip(),
            options=json.dumps([option.strip() for option in item.options], ensure_ascii=False),
            correct_option=item.correct_option,
            explanation=item.explanation or "Comentário editorial pendente.",
            source=payload.source_name,
            is_published=can_publish,
        )
        db.add(question)
        db.flush()
        db.add(QuestionProvenance(
            question_id=question.id,
            external_key=item.external_key,
            content_hash=digest,
            source_name=payload.source_name,
            source_url=str(payload.source_url) if payload.source_url else None,
            organization=payload.organization,
            board=payload.board,
            exam_year=payload.exam_year,
            rights_status=payload.rights_status,
            import_batch=payload.import_batch,
        ))
        imported += 1
    db.commit()
    return {
        "imported": imported,
        "duplicates": duplicates,
        "rejected": rejected,
        "published": imported if can_publish else 0,
        "review_required": 0 if can_publish else imported,
    }
