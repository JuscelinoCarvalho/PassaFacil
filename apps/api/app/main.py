from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import inspect, text

from app.api.routes import auth, billing, discursive, exams, feedback, health, question_bank, reviews, simulations, study
from app.core.config import settings
from app.db.base import Base
from app.db.seed import seed_tce_sp
from app.db.session import SessionLocal, engine
from app import models  # noqa: F401


def _ensure_columns() -> None:
    """Micro-migração idempotente: create_all() cria tabelas novas mas não adiciona
    colunas a tabelas existentes. Adiciona as colunas de conversão server-side do
    Google Ads (gclid etc.) sem depender de Alembic. ADD COLUMN funciona em
    Postgres (produção) e SQLite (dev)."""
    is_sqlite = engine.dialect.name == "sqlite"
    false_default = "0" if is_sqlite else "false"
    additions = {
        "gclid": "VARCHAR(512)",
        "conversion_uploaded": f"BOOLEAN DEFAULT {false_default}",
        "conversion_upload_error": "TEXT",
    }
    # Colunas da correção por IA das discursivas (Fase 2). JSON funciona em
    # Postgres (produção) e SQLite (dev, afinidade dinâmica).
    disc_additions = {
        "ai_scores": "JSON",
        "ai_total": "NUMERIC(5, 2)",
        "ai_feedback": "JSON",
        "ai_comentario": "TEXT",
        "ai_provider": "VARCHAR(40)",
    }
    plan = [("subscriptions", additions), ("discursive_submissions", disc_additions)]
    for table, cols in plan:
        try:
            existing = {c["name"] for c in inspect(engine).get_columns(table)}
        except Exception:  # noqa: BLE001 — tabela ainda não existe: create_all cuida
            continue
        with engine.begin() as conn:
            for name, ddl in cols.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))


TRIAL_EVENT_RETENTION_DAYS = 180  # LGPD: retenção limitada da telemetria anônima


def _purge_old_trial_events() -> None:
    """Expurga telemetria anônima do teste grátis mais velha que a janela de retenção.
    Best-effort — não quebra o startup se a tabela ainda não existir."""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=TRIAL_EVENT_RETENTION_DAYS)
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM trial_events WHERE created_at < :cutoff"), {"cutoff": cutoff})
    except Exception:  # noqa: BLE001
        pass


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    _ensure_columns()
    _purge_old_trial_events()
    with SessionLocal() as db:
        seed_tce_sp(db)
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="API do Passa Fácil — estudo adaptativo para concursos.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def disable_api_cache(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith(settings.api_v1_prefix):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response
app.include_router(health.router)
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(exams.router, prefix=settings.api_v1_prefix)
app.include_router(study.router, prefix=settings.api_v1_prefix)
app.include_router(reviews.router, prefix=settings.api_v1_prefix)
app.include_router(simulations.router, prefix=settings.api_v1_prefix)
app.include_router(question_bank.router, prefix=settings.api_v1_prefix)
app.include_router(billing.router, prefix=settings.api_v1_prefix)
app.include_router(discursive.router, prefix=settings.api_v1_prefix)
app.include_router(feedback.router, prefix=settings.api_v1_prefix)
