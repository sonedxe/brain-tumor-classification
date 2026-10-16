"""Motor y sesion de base de datos (SQLite)."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

_is_sqlite = settings.database_url.startswith("sqlite")

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Crea las tablas y siembra los catalogos de referencia."""
    import app.models  # noqa: F401  (registra todas las tablas en Base.metadata)

    from app.db.base import Base
    from app.db.seed import seed_reference_data

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        seed_reference_data(db)
