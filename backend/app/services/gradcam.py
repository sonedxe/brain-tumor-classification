"""Generacion de mapas de calor Grad-CAM para el servicio de inferencia.

Reutiliza `ml/evaluation/gradcam.py`, que ya resuelve la capa objetivo de cada
arquitectura a partir de `gradcam_target_layer` en los YAML de ml/configs/.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class GradCamService:
    def __init__(self, output_dir: Path | None = None, static_url: str | None = None) -> None:
        self.output_dir = output_dir or (settings.media_root / "gradcam")
        self.static_url = static_url or settings.static_url

    def ensure_ready(self) -> None:
        raise NotImplementedError(
            "Integrar aqui pytorch_grad_cam sobre el modelo cargado en "
            "services/inference.py, usando ml/evaluation/gradcam.py"
        )

    def output_path_for(self, image_hash: str) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir / f"{image_hash[:16]}.png"

    def public_path(self, file_path: Path) -> str:
        return f"{self.static_url}/{file_path.name}"

    def generate(self, image, model) -> str:
        raise NotImplementedError("Ver ensure_ready()")
