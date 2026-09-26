"""Servicio de inferencia.

La implementacion real se conecta con `ml/training/train.py` y
`ml/evaluation/gradcam.py`. Mientras tanto, con MOCK_INFERENCE=true devuelve una
respuesta ficticia para poder construir y probar el frontend sin esperar a que
termine el entrenamiento.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

import numpy as np

from app.core.constants import CLASSES

logger = logging.getLogger(__name__)

_EPS = 1e-6


class InferenceService:
    def __init__(self, model_path=None, model_version: str = "unknown", enable_gradcam: bool = True, mock: bool = True) -> None:
        self.model_path = model_path
        self.model_version = model_version
        self.enable_gradcam = enable_gradcam
        self.mock = mock
        self._model: Any | None = None
        self._gradcam: Any | None = None

    @property
    def is_ready(self) -> bool:
        return self._model is not None

    def load(self) -> None:
        """Carga los pesos entrenados. Punto unico de integracion con ml/."""
        raise NotImplementedError(
            "Integrar aqui la carga de pesos desde ml/models/<modelo>/best.pt "
            "usando timm.create_model(pretrained=False) + load_state_dict"
        )

    def predict(self, image: np.ndarray) -> dict[str, Any]:
        if self.is_ready:
            return self._predict_real(image)
        if self.mock:
            return self._predict_mock(image)
        raise NotImplementedError("No hay pesos cargados y MOCK_INFERENCE esta en false")

    def _predict_real(self, image: np.ndarray) -> dict[str, Any]:
        raise NotImplementedError("Implementar la pasada hacia adelante del modelo")

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
        if not self.enable_gradcam or self._gradcam is None:
            return None
        raise NotImplementedError("Implementar la generacion del mapa de calor")
