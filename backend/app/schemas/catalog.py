"""Esquemas de los catalogos (modelos y clases)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class MLModelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    architecture: str
    version: str
    dataset: str
    num_parameters_m: float | None = None
    accuracy: float | None = None
    macro_f1: float | None = None
    roc_auc: float | None = None
    is_active: bool


class LesionClassRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    display_name: str
    index: int
    is_tumor: bool
    description: str | None = None


class ImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sha256: str
    width: int
    height: int
    format: str
    size_bytes: int
