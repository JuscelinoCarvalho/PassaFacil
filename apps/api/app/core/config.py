from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Passa Fácil API"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./passafacil.db"
    jwt_secret: str = "local-development-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://localhost:9001"
    owner_mode: bool = True
    owner_email: str = "juscelino@passafacil.local"
    question_import_dir: str = "./data/imports"
    max_pdf_upload_mb: int = 50

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
