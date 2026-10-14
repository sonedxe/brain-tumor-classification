"""Configuracion compartida de las pruebas."""

from __future__ import annotations

import os
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db.sqlite3")

os.environ["MEDIA_ROOT"] = str(Path(__file__).resolve().parents[1] / "media")


def _ensure_test_checkpoint() -> Path:
    """Crea (una vez) un checkpoint torchvision minimo para las pruebas.

    Pesos aleatorios: no se depende de los pesos entrenados reales (que no se
    versionan), pero la ruta de inferencia es la misma que en produccion.
    """
    path = Path(tempfile.gettempdir()) / "btc_test_best.pt"
    if not path.exists():
        import torch

        from app.core.constants import CLASSES
        from app.services.model_factory import build_model

        model = build_model("shufflenetv2", num_classes=len(CLASSES), pretrained=False)
        torch.save(
            {
                "architecture": "shufflenetv2",
                "state_dict": model.state_dict(),
                "classes": list(CLASSES),
                "class_to_idx": {name: i for i, name in enumerate(CLASSES)},
                "input_size": 224,
                "normalization": {
                    "mode": "imagenet",
                    "mean": [0.485, 0.456, 0.406],
                    "std": [0.229, 0.224, 0.225],
                },
            },
            path,
        )
    return path


os.environ["MODEL_PATH"] = str(_ensure_test_checkpoint())

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
