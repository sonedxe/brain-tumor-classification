"""Generacion del informe clinico en PDF (una pagina A4).

Usa fuentes base de fpdf2 (latin-1): cubre tildes y enies del espanol sin
depender de archivos de fuente externos. Todo texto pasa por `_safe` para
descartar caracteres fuera de latin-1 en lugar de fallar con un 500.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from fpdf import FPDF

from app.core.config import get_settings
from app.models.prediction import Prediction

logger = logging.getLogger(__name__)

CLASS_ORDER = ("glioma", "meningioma", "no_tumor", "pituitario")

CLINICAL_DESCRIPTIONS = {
    "glioma": (
        "Tumor primario originado en las celulas gliales del sistema nervioso "
        "central. Se recomienda valoracion prioritaria por neurologia o "
        "neurocirugia y estudios complementarios."
    ),
    "meningioma": (
        "Tumor que se origina en las meninges. Con frecuencia es de crecimiento "
        "lento; se sugiere correlacion clinica y seguimiento por especialista."
    ),
    "pituitario": (
        "Lesion de la glandula pituitaria (hipofisis). Se sugiere evaluacion "
        "endocrinologica y control por neurocirugia o neuroendocrinologia."
    ),
    "no_tumor": (
        "Sin hallazgos tumorales segun el modelo. Un resultado negativo no "
        "descarta patologia: ante sintomas persistentes consulte al especialista."
    ),
}

DISCLAIMER = (
    "AVISO: este informe es un apoyo al diagnostico generado por un modelo de "
    "aprendizaje profundo con fines academicos. No constituye un diagnostico "
    "medico ni reemplaza el criterio de un profesional de la salud. Toda "
    "decision clinica debe ser validada por un medico especialista."
)

_CLASS_COLORS = {
    "glioma": (220, 53, 69),
    "meningioma": (245, 158, 11),
    "pituitario": (124, 58, 237),
    "no_tumor": (22, 163, 74),
}


def _safe(text: object) -> str:
    return str(text).encode("latin-1", "replace").decode("latin-1")


class PDFReportService:
    def __init__(self, media_root: Path | None = None) -> None:
        self.media_root = Path(media_root or get_settings().media_root)

    # --- resolucion segura de imagenes -------------------------------------
    def _resolve_media(self, relative: str | None) -> Path | None:
        """Convierte `/static/x/y.png` en una ruta bajo media_root, o None.

        Rechaza rutas que escapen de media_root y archivos inexistentes.
        """
        if not relative:
            return None
        static_url = get_settings().static_url
        rel = relative[len(static_url):] if relative.startswith(static_url) else relative
        candidate = (self.media_root / rel.lstrip("/\\")).resolve()
        try:
            candidate.relative_to(self.media_root.resolve())
        except ValueError:
            return None
        return candidate if candidate.is_file() else None

    def _original_path(self, prediction: Prediction) -> Path | None:
        """La API no persiste la MRI original (privacidad); solo se usa si un
        despliegue la dejo en media/originals/<sha256>.<ext>."""
        folder = self.media_root / "originals"
        for ext in ("png", "jpg", "jpeg"):
            path = folder / f"{prediction.image_hash}.{ext}"
            if path.is_file():
                return path
        return None

    @staticmethod
    def _draw_image(
        pdf: FPDF, path: Path | None, x: float, y: float, size: float, missing: str
    ) -> None:
        pdf.set_draw_color(180, 188, 200)
        pdf.rect(x, y, size, size)
        if path is not None:
            try:
                pdf.image(str(path), x=x, y=y, w=size, h=size, keep_aspect_ratio=True)
                return
            except Exception:  # imagen corrupta: degradar a placeholder
                logger.warning("No se pudo incrustar %s en el PDF", path)
        pdf.set_xy(x, y + size / 2 - 4)
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(120, 128, 140)
        pdf.multi_cell(size, 4.5, _safe(missing), align="C")

    # --- generacion ---------------------------------------------------------
    def generate(self, prediction: Prediction, user_label: str | None = None) -> bytes:
        pdf = FPDF(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=False)
        pdf.set_margins(15, 15, 15)
        pdf.add_page()
        label = prediction.label

        # Encabezado
        pdf.set_fill_color(15, 23, 42)
        pdf.rect(0, 0, 210, 28, style="F")
        pdf.set_xy(15, 7)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(
            0, 7, "Informe clinico - Clasificacion de tumores cerebrales",
            new_x="LMARGIN", new_y="NEXT",
        )
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5, f"Emitido: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

        # Metadatos
        pdf.set_xy(15, 35)
        pdf.set_text_color(15, 23, 42)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 6, "Datos del estudio", new_x="LMARGIN", new_y="NEXT")
        created = (
            prediction.created_at.strftime("%d/%m/%Y %H:%M") if prediction.created_at else "-"
        )
        meta = [
            ("ID de prediccion", f"#{prediction.id}"),
            ("Usuario", user_label or "No registrado"),
            ("Modelo", prediction.model_version),
            ("Tiempo de inferencia", f"{prediction.inference_ms:.1f} ms"),
            ("Fecha del analisis", created),
            ("Huella de imagen", prediction.image_hash[:16] + "..."),
        ]
        pdf.set_font("Helvetica", "", 10)
        for key, value in meta:
            pdf.set_text_color(90, 98, 112)
            pdf.cell(48, 5.5, _safe(key))
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 5.5, _safe(value), new_x="LMARGIN", new_y="NEXT")

        # Imagenes lado a lado
        top = pdf.get_y() + 4
        size = 80
        pdf.set_xy(15, top)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(size, 5, "MRI original")
        pdf.set_x(15 + size + 10)
        pdf.cell(size, 5, "Mapa de calor Grad-CAM", new_x="LMARGIN", new_y="NEXT")
        self._draw_image(
            pdf, self._original_path(prediction), 15, top + 6, size,
            "MRI original no almacenada\n(politica de privacidad)",
        )
        self._draw_image(
            pdf, self._resolve_media(prediction.gradcam_path), 15 + size + 10, top + 6, size,
            "Grad-CAM no disponible",
        )

        # Resultado
        y = top + 6 + size + 6
        color = _CLASS_COLORS.get(label, (15, 23, 42))
        pdf.set_xy(15, y)
        pdf.set_fill_color(*color)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(
            0, 9,
            _safe(
                f"  Resultado: {prediction.predicted_class.display_name}"
                f"  |  Confianza {prediction.confidence * 100:.1f} %"
            ),
            fill=True, new_x="LMARGIN", new_y="NEXT",
        )

        # Distribucion de probabilidades
        probs = {s.lesion_class.code: s.probability for s in prediction.scores}
        names = {s.lesion_class.code: s.lesion_class.display_name for s in prediction.scores}
        pdf.ln(3)
        pdf.set_text_color(15, 23, 42)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "Distribucion de probabilidades", new_x="LMARGIN", new_y="NEXT")
        bar_x, bar_w = 62, 100
        for code in CLASS_ORDER:
            value = probs.get(code, 0.0)
            row_y = pdf.get_y()
            highlighted = code == label
            pdf.set_font("Helvetica", "B" if highlighted else "", 10)
            pdf.set_text_color(15, 23, 42)
            pdf.set_xy(15, row_y)
            pdf.cell(45, 6, _safe(names.get(code, code) + (" (predicha)" if highlighted else "")))
            pdf.set_fill_color(230, 233, 239)
            pdf.rect(bar_x, row_y + 1, bar_w, 4, style="F")
            pdf.set_fill_color(*(_CLASS_COLORS[code] if highlighted else (150, 160, 175)))
            pdf.rect(bar_x, row_y + 1, max(bar_w * value, 0.3), 4, style="F")
            pdf.set_xy(bar_x + bar_w + 3, row_y)
            pdf.cell(0, 6, f"{value * 100:.1f} %", new_x="LMARGIN", new_y="NEXT")

        # Descripcion clinica
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_x(15)
        pdf.cell(0, 6, "Descripcion clinica", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(
            0, 5,
            _safe(CLINICAL_DESCRIPTIONS.get(label, prediction.predicted_class.description or "")),
        )

        # Pie
        pdf.set_draw_color(180, 188, 200)
        pdf.line(15, 271, 195, 271)
        pdf.set_xy(15, 272)
        pdf.set_font("Helvetica", "I", 7.5)
        pdf.set_text_color(110, 118, 130)
        pdf.multi_cell(0, 3.6, _safe(DISCLAIMER))

        return bytes(pdf.output())
