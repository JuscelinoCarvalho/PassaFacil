from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, exams, health, question_bank, reviews, simulations, study
from app.core.config import settings
from app.db.base import Base
from app.db.seed import seed_tce_sp
from app.db.session import SessionLocal, engine
from app import models  # noqa: F401


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
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
