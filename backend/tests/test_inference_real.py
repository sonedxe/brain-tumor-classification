"""Pruebas de la inferencia real (sin mock).

Crean un checkpoint torchvision miniatura con pesos aleatorios y verifican que
`InferenceService` lo carga, predice y genera un Grad-CAM valido, sin depender
de los pesos entrenados reales (que no se versionan). Requieren PyTorch; si no
esta instalado, se omiten para no romper la suite en modo mock.
"""

from __future__ import annotations

import numpy as np
import pytest

from app.core.constants import CLASSES
from app.services.inference import InferenceService

torch = pytest.importorskip("torch")

# Architecture chosen for its small checkpoint size (fast to write/read).
ARCHITECTURE = "shufflenetv2"


@pytest.fixture
def checkpoint_path(tmp_path):
    from app.services.model_factory import build_model

    model = build_model(ARCHITECTURE, num_classes=len(CLASSES), pretrained=False)
    path = tmp_path / "best.pt"
    torch.save(
        {
            "architecture": ARCHITECTURE,
            "state_dict": model.state_dict(),
            "classes": list(CLASSES),
            "class_to_idx": {name: index for index, name in enumerate(CLASSES)},
            "epoch": 1,
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


@pytest.fixture
def image() -> np.ndarray:
    rng = np.random.default_rng(42)
    return rng.integers(0, 255, size=(224, 224, 3), dtype=np.uint8).astype(np.float32)


def test_loads_checkpoint_and_predicts(checkpoint_path, image):
    service = InferenceService(
        model_path=checkpoint_path, model_version="shufflenetv2-test", mock=False
    )
    service.load()

    assert service.is_ready is True

    result = service.predict(image)
    assert result["label"] in CLASSES
    assert set(result["probabilities"]) == set(CLASSES)
    assert sum(result["probabilities"].values()) == pytest.approx(1.0, abs=1e-4)
    assert result["confidence"] == pytest.approx(
        result["probabilities"][result["label"]], abs=1e-4
    )


def test_generates_gradcam_png(checkpoint_path, image, tmp_path):
    from PIL import Image

    service = InferenceService(
        model_path=checkpoint_path, model_version="shufflenetv2-test", mock=False
    )
    service.load()

    result = service.predict(image)
    assert result["gradcam_path"] is not None
    assert result["gradcam_path"].startswith("/static/gradcam/")

    from app.core.config import get_settings

    filename = result["gradcam_path"].rsplit("/", 1)[-1]
    output = get_settings().media_root / "gradcam" / filename
    assert output.exists()
    with Image.open(output) as png:
        assert png.size == (224, 224)


def test_predict_is_deterministic_with_real_weights(checkpoint_path, image):
    service = InferenceService(
        model_path=checkpoint_path, model_version="shufflenetv2-test", mock=False
    )
    service.load()
    first = service.predict(image)
    second = service.predict(image)
    assert first["label"] == second["label"]
    assert first["probabilities"] == second["probabilities"]


def test_missing_weights_without_mock_raises(tmp_path):
    service = InferenceService(
        model_path=tmp_path / "does-not-exist.pt", model_version="x", mock=False
    )
    with pytest.raises(FileNotFoundError):
        service.load()


def test_predict_without_weights_and_without_mock_raises(image):
    service = InferenceService(model_path=None, model_version="x", mock=False)
    with pytest.raises(RuntimeError):
        service.predict(image)


@pytest.mark.parametrize("architecture", sorted(
    ["mobilenetv3", "efficientnetb0", "shufflenetv2", "densenet121", "resnet18"]
))
def test_gradcam_target_layer_resolves(architecture):
    from app.services.model_factory import (
        GRADCAM_TARGET_LAYERS,
        build_model,
        resolve_target_layers,
    )

    model = build_model(architecture, num_classes=len(CLASSES), pretrained=False)
    layers = resolve_target_layers(model, GRADCAM_TARGET_LAYERS[architecture])
    assert len(layers) == 1
    # La capa objetivo puede ser una Conv2d, un bloque residual o un Sequential;
    # lo importante es que sea un modulo donde enganchar los hooks.
    assert isinstance(layers[0], torch.nn.Module)
