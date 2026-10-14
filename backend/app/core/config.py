"""Configuracion de la aplicacion, leida desde variables de entorno o .env."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Brain Tumor Classification API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"

    model_path: Path = REPO_ROOT / "ml" / "models" / "mobilenetv3" / "best.pt"
    model_version: str = "mobilenetv3-v1"
    image_size: int = 224
    enable_gradcam: bool = True

    @field_validator("model_path", "media_root", mode="after")
    @classmethod
    def _resolve_against_repo_root(cls, value: Path) -> Path:
        """Resuelve rutas relativas (p. ej. MODEL_PATH en .env) contra la raiz
        del repositorio, de modo que no dependan del directorio de ejecucion."""
        return value if value.is_absolute() else (REPO_ROOT / value)

    database_url: str = f"sqlite:///{BACKEND_DIR / 'db.sqlite3'}"
    max_upload_bytes: int = 10 * 1024 * 1024
    media_root: Path = BACKEND_DIR / "media"
    static_url: str = "/static"

    # Autenticacion (camino opcional). En produccion define JWT_SECRET propio.
    jwt_secret: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7  # 7 dias

    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    # Origenes de desarrollo: Flutter web sirve en http://localhost:<puerto>.
    cors_origin_regex: str = r"http://(localhost|127\.0\.0\.1)(:\d+)?"


@lru_cache
def get_settings() -> Settings:
    return Settings()
