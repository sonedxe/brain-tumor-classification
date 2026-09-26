"""Configuracion compartida de las pruebas."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest

os.environ.setdefault("MOCK_INFERENCE", "true")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db.sqlite3")

os.environ["MEDIA_ROOT"] = str(Path(__file__).resolve().parents[1] / "media")

from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def settings():
    return get_settings()


@pytest.fixture
def db_session() -> Iterator:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_database() -> Iterator[None]:
    """Vacia la base antes y despues de cada prueba.

    Sin esto, los registros de un test contaminan al siguiente y las
    aserciones sobre el historial dan falsos negativos.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_image_bytes() -> bytes:
    import io

    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (256, 256), color=(120, 130, 140)).save(buffer, format="JPEG")
    return buffer.getvalue()
