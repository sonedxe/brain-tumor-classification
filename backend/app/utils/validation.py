"""Validacion de la imagen subida."""

from __future__ import annotations

import io

from PIL import Image, UnidentifiedImageError

ALLOWED_FORMATS = frozenset({"JPEG", "PNG", "BMP", "WEBP", "TIFF"})
MIN_SIDE = 32
MAX_SIDE = 4096


class InvalidImageError(ValueError):
    def __init__(self, detail: str, status_code: int = 400) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def ensure_valid_image(raw: bytes, max_bytes: int) -> None:
    if not raw:
        raise InvalidImageError("El archivo enviado esta vacio")

    if len(raw) > max_bytes:
        raise InvalidImageError(
            f"El archivo supera el limite de {max_bytes} bytes", status_code=413
        )

    try:
        with Image.open(io.BytesIO(raw)) as image:
            image.verify()
    except UnidentifiedImageError as exc:
        raise InvalidImageError("El archivo no es una imagen legible") from exc
    except (OSError, ValueError) as exc:
        raise InvalidImageError("La imagen esta corrupta o es un formato no soportado") from exc

    try:
        with Image.open(io.BytesIO(raw)) as image:
            fmt = (image.format or "").upper()
            width, height = image.size
    except (OSError, ValueError) as exc:
        raise InvalidImageError("No se pudieron leer las dimensiones de la imagen") from exc

    if fmt not in ALLOWED_FORMATS:
        raise InvalidImageError(
            f"Formato {fmt or 'desconocido'} no permitido. Admitidos: "
            f"{', '.join(sorted(ALLOWED_FORMATS))}"
        )

    if width < MIN_SIDE or height < MIN_SIDE:
        raise InvalidImageError(f"La imagen es demasiado pequena ({width}x{height})")

    if width > MAX_SIDE or height > MAX_SIDE:
        raise InvalidImageError(f"La imagen es demasiado grande ({width}x{height})")
