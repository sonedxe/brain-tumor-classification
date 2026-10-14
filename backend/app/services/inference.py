"""Servicio de inferencia (OE3).

Modo real: carga `ml/models/<modelo>/best.pt` (checkpoint torchvision con las
claves `architecture`, `state_dict`, `classes`, `normalization` e `input_size`
que produce `ml/training/train.py`) y ejecuta la pasada hacia adelante.

Modo mock (`MOCK_INFERENCE=true`): si no hay pesos en disco, devuelve una
respuesta ficticia pero determinista, derivada del contenido de la imagen, para
poder construir y probar el frontend sin esperar al entrenamiento.

La carga real intenta primero el checkpoint; solo cae al mock cuando el archivo
no existe y `MOCK_INFERENCE` esta activo. Con `MOCK_INFERENCE=false` y sin
pesos, `load()` falla en voz alta en lugar de simular.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from app.core.constants import CLASSES
from app.services.gradcam import GradCamService

logger = logging.getLogger(__name__)

_EPS = 1e-6
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


class InferenceService:
    def __init__(
        self,
        model_path: Path | str | None = None,
        model_version: str = "unknown",
        enable_gradcam: bool = True,
        mock: bool = True,
    ) -> None:
        self.model_path = Path(model_path) if model_path else None
        self.model_version = model_version
        self.enable_gradcam = enable_gradcam
        self.mock = mock
        self._model: Any | None = None
        self._gradcam: GradCamService | None = None
        self._classes: tuple[str, ...] = tuple(CLASSES)
        self._input_size: int = 224
        self._normalization: dict[str, list[float]] = {
            "mean": IMAGENET_MEAN,
            "std": IMAGENET_STD,
        }

    @property
    def is_ready(self) -> bool:
        return self._model is not None

    @property
    def classes(self) -> tuple[str, ...]:
        return self._classes

    def load(self) -> None:
        """Carga los pesos entrenados si existen.

        Es el punto de integracion con `ml/`: al dejar `best.pt` en la ruta de
        `MODEL_PATH`, el backend pasa de mock a inferencia real sin tocar el
        contrato HTTP.
        """
        if self._model is not None:
            return

        if self.model_path is None or not self.model_path.exists():
            if self.mock:
                logger.warning(
                    "Pesos no encontrados en %s; la inferencia seguira en modo mock",
                    self.model_path,
                )
                return
            raise FileNotFoundError(
                f"No hay pesos en {self.model_path} y MOCK_INFERENCE esta desactivado"
            )

        import torch

        from app.services.model_factory import (
            GRADCAM_TARGET_LAYERS,
            build_model,
            resolve_target_layers,
        )

        checkpoint = torch.load(self.model_path, map_location="cpu", weights_only=False)
        if not isinstance(checkpoint, dict) or "state_dict" not in checkpoint:
            raise ValueError(
                f"{self.model_path} no es un checkpoint valido: falta 'state_dict'"
            )

        architecture = checkpoint.get("architecture", "")
        classes = tuple(checkpoint.get("classes") or CLASSES)
        normalization = checkpoint.get("normalization") or {
            "mean": IMAGENET_MEAN,
            "std": IMAGENET_STD,
        }

        model = build_model(architecture, num_classes=len(classes), pretrained=False)
        model.load_state_dict(checkpoint["state_dict"])
        model.eval()

        self._model = model
        self._classes = classes
        self._input_size = int(checkpoint.get("input_size", 224))
        self._normalization = normalization
        if checkpoint.get("model_version"):
            self.model_version = checkpoint["model_version"]

        if self.enable_gradcam:
            self._gradcam = GradCamService()
            self._gradcam.ensure_ready(
                model, resolve_target_layers(model, GRADCAM_TARGET_LAYERS.get(architecture))
            )

        logger.info(
            "Modelo %s cargado desde %s (clases=%s, entrada=%dx%d)",
            architecture,
            self.model_path,
            list(classes),
            self._input_size,
            self._input_size,
        )

    def predict(self, image: np.ndarray) -> dict[str, Any]:
        if self.is_ready:
            return self._predict_real(image)
        if self.mock:
            return self._predict_mock(image)
        raise RuntimeError("No hay pesos cargados y MOCK_INFERENCE esta desactivado")

    def _to_tensor(self, image: np.ndarray, requires_grad: bool = False) -> Any:
        """Convierte HWC float32 0-255 a un tensor NCHW normalizado."""
        import torch

        mean = np.asarray(self._normalization["mean"], dtype=np.float32).reshape(1, 3, 1, 1)
        std = np.asarray(self._normalization["std"], dtype=np.float32).reshape(1, 3, 1, 1)
        chw = np.transpose(np.asarray(image, dtype=np.float32), (2, 0, 1))[np.newaxis, ...]
        array = ((chw / 255.0) - mean) / std
        tensor = torch.from_numpy(array)
        if requires_grad:
            tensor.requires_grad_(True)
        return tensor

    def _predict_real(self, image: np.ndarray) -> dict[str, Any]:
        import torch

        image = self._ensure_size(image)
        with torch.no_grad():
            logits = self._model(self._to_tensor(image))
            probabilities = torch.softmax(logits, dim=1)[0].cpu().numpy()

        index = int(probabilities.argmax())

        gradcam_path = None
        if self.enable_gradcam and self._gradcam is not None and self._gradcam.is_ready:
            try:
                original = Image.fromarray(np.uint8(np.clip(image, 0, 255)))
                gradcam_path = self._gradcam.generate(
                    original, self._to_tensor(image, requires_grad=True), index
                )
            except Exception:  # pragma: no cover - el mapa no debe romper la prediccion
                logger.exception("No se pudo generar el Grad-CAM; se omite")

        return {
            "label": self._classes[index],
            "confidence": float(probabilities[index]),
            "probabilities": {
                name: float(probabilities[i]) for i, name in enumerate(self._classes)
            },
            "gradcam_path": gradcam_path,
        }

    def _ensure_size(self, image: np.ndarray) -> np.ndarray:
        if image.shape[0] == self._input_size and image.shape[1] == self._input_size:
            return image
        resized = Image.fromarray(np.uint8(np.clip(image, 0, 255))).resize(
            (self._input_size, self._input_size), Image.BILINEAR
        )
        return np.asarray(resized, dtype=np.float32)

    def _predict_mock(self, image: np.ndarray) -> dict[str, Any]:
        """Respuesta deterministica derivada del contenido de la imagen.

        Determinista a proposito: dos cargas de la misma imagen devuelven
        siempre el mismo resultado, de modo que las pruebas de la interfaz no
        son intermitentes.
        """
        digest = hashlib.sha256(image.tobytes()).digest()
        weights = np.frombuffer(digest, dtype=np.uint8, count=len(CLASSES)).astype(np.float64)
        weights += _EPS
        probabilities = weights / weights.sum()
        index = int(probabilities.argmax())

        return {
            "label": CLASSES[index],
            "confidence": float(probabilities[index]),
            "probabilities": {name: float(p) for name, p in zip(CLASSES, probabilities)},
            "gradcam_path": None,
        }

    def gradcam(self, image: np.ndarray) -> str | None:
        if not self.enable_gradcam or self._gradcam is None or not self._gradcam.is_ready:
            return None
        import torch

        image = self._ensure_size(image)
        with torch.no_grad():
            logits = self._model(self._to_tensor(image))
        index = int(logits.argmax(dim=1).item())
        original = Image.fromarray(np.uint8(np.clip(image, 0, 255)))
        return self._gradcam.generate(original, self._to_tensor(image, requires_grad=True), index)
