"""Figuras embutidas em questões (sequências figurais, gráficos, prints).

A `Question.image_url` guarda apenas o NOME do arquivo (ex.: "quest9Raciocinio.jpg");
o binário fica em `apps/api/media/question_assets/`. A URL servível é montada por
`question_asset_url` e servida por `GET /api/v1/study/question-asset/{name}` (study.py),
no mesmo padrão do áudio-piloto. Mantemos só o nome no banco para não acoplar a URL/prefixo.
"""

from pathlib import Path

# apps/api/media/question_assets  (parents[2] = app/ -> apps/api/app; subir 1 = apps/api)
QUESTION_ASSET_DIR = Path(__file__).resolve().parents[2] / "media" / "question_assets"

# Extensões aceitas -> content-type (evita servir qualquer coisa do diretório).
ALLOWED_ASSET_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".svg": "image/svg+xml",
}


def question_asset_url(name: str | None) -> str | None:
    """URL pública para o front, ou None se a questão não tem figura."""
    if not name:
        return None
    return f"/api/v1/study/question-asset/{Path(name).name}"


def resolve_asset(name: str) -> tuple[Path, str] | None:
    """Resolve um nome de arquivo para (caminho, content-type) de forma segura
    (bloqueia path traversal e tipos não permitidos). None se inválido/inexistente."""
    safe = Path(name).name
    if safe != name:
        return None
    ctype = ALLOWED_ASSET_TYPES.get(Path(safe).suffix.lower())
    if not ctype:
        return None
    path = QUESTION_ASSET_DIR / safe
    if not path.exists() or not path.is_file():
        return None
    return path, ctype
