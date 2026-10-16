"""Esquemas del feedback humano sobre una prediccion."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.catalog import LesionClassRead


class FeedbackCreate(BaseModel):
    is_correct: bool = Field(description="El revisor confirma o corrige la etiqueta")
    corrected_label: str | None = Field(
        default=None,
        description="Codigo de la clase correcta (glioma, meningioma, pituitario, no_tumor)",
    )
    comment: str | None = Field(default=None, max_length=255)


class FeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_correct: bool
    comment: str | None = None
    created_at: datetime
    corrected_class: LesionClassRead | None = None
