"""Generacion de mapas de calor Grad-CAM para el servicio de inferencia (OE2).

Implementacion autocontenida basada en *hooks* de PyTorch, para no arrastrar
`opencv-python` ni `pytorch-grad-cam` a la imagen del backend. Reproduce el
comportamiento de `ml/evaluation/gradcam.py`: la capa objetivo se resuelve por
arquitectura (ver `model_factory.GRADCAM_TARGET_LAYERS`) y el mapa se superpone
a la imagen con un colormap tipo *jet*.

El mapa solo depende del modelo y de la clase predicha, de modo que el archivo
generado es reproducible para la misma imagen.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
_EPS = 1e-8


def _jet_colormap(heatmap: np.ndarray) -> np.ndarray:
    """Aproximacion del colormap 'jet' en [0, 1] -> HWC float RGB."""
    r = np.clip(1.5 - np.abs(4.0 * heatmap - 3.0), 0.0, 1.0)
    g = np.clip(1.5 - np.abs(4.0 * heatmap - 2.0), 0.0, 1.0)
    b = np.clip(1.5 - np.abs(4.0 * heatmap - 1.0), 0.0, 1.0)
    return np.stack([r, g, b], axis=-1)


def overlay_heatmap(original: Image.Image, heatmap: np.ndarray, alpha: float = 0.45) -> Image.Image:
    """Superpone el mapa de calor a la imagen original."""
    rgb = Image.fromarray(np.uint8(255.0 * _jet_colormap(heatmap))).resize(original.size)
    heatmap_rgb = np.asarray(rgb, dtype=np.float32)

    base = np.asarray(original.convert("RGB"), dtype=np.float32)
    blended = (1.0 - alpha) * base + alpha * heatmap_rgb
    return Image.fromarray(np.uint8(np.clip(blended, 0, 255)))


class GradCamService:
    def __init__(self, output_dir: Path | None = None, static_url: str | None = None) -> None:
        self.output_dir = output_dir or (settings.media_root / "gradcam")
        self.static_url = static_url or settings.static_url
        self._model: Any | None = None
        self._target_layers: list[Any] = []

    def ensure_ready(self, model: Any, target_layers: list[Any]) -> None:
        """Registra el modelo y las capas objetivo que se usaran en generate()."""
        self._model = model
        self._target_layers = list(target_layers)

    @property
    def is_ready(self) -> bool:
        return self._model is not None and bool(self._target_layers)

    def output_path_for(self, image_hash: str) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir / f"{image_hash[:16]}.png"

    def public_path(self, file_path: Path) -> str:
        return f"{self.static_url}/gradcam/{file_path.name}"

    def generate(self, image: Image.Image, tensor: Any, class_index: int) -> str:
        """Genera el Grad-CAM de `class_index` y devuelve su ruta publica /static/...

        `image` es la imagen original (para superponer) y `tensor` un tensor NCHW
        de 1 elemento creado con gradiente habilitado.
        """
        if not self.is_ready:
            raise RuntimeError("GradCamService no esta listo: falta ensure_ready()")

        import torch

        activations: dict[str, Any] = {}
        gradients: dict[str, Any] = {}

        def _forward(_module, _inputs, output):
            activations["value"] = output

        def _backward(_module, _grad_input, grad_output):
            gradients["value"] = grad_output[0]

        handles = []
        for layer in self._target_layers:
            handles.append(layer.register_forward_hook(_forward))
            handles.append(layer.register_full_backward_hook(_backward))

        try:
            self._model.zero_grad(set_to_none=True)
            logits = self._model(tensor)
            logits[0, class_index].backward()

            gradients_value = gradients["value"]
            activations_value = activations["value"]
            weights = gradients_value.mean(dim=(2, 3), keepdim=True)
            cam = torch.relu((weights * activations_value).sum(dim=1, keepdim=True))
            cam = cam - cam.amin(dim=(2, 3), keepdim=True)
            cam = cam / (cam.amax(dim=(2, 3), keepdim=True) + _EPS)
            heatmap = cam[0, 0].detach().cpu().numpy()
        finally:
            for handle in handles:
                handle.remove()

        digest = hashlib.sha256(image.tobytes()).hexdigest()
        file_path = self.output_path_for(digest)
        overlay_heatmap(image, heatmap).save(file_path)
        logger.info("Grad-CAM generado en %s", file_path)
        return self.public_path(file_path)
