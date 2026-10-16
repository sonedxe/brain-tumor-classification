"""Repositorio de catalogos: imagenes, clases y modelos.

Los catalogos se resuelven con *get-or-create* porque la primera vez que llega
una imagen o un modelo hay que crear la fila, pero a partir de ahi debe
reutilizarse (una imagen repetida no se inserta dos veces).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.image import Image
from app.models.lesion_class import LesionClass
from app.models.ml_model import MLModel


def get_or_create_image(
    db: Session,
    *,
    sha256: str,
    width: int,
    height: int,
    image_format: str,
    size_bytes: int,
) -> Image:
    image = db.scalar(select(Image).where(Image.sha256 == sha256))
    if image is not None:
        return image

    image = Image(
        sha256=sha256,
        width=width,
        height=height,
        format=image_format,
        size_bytes=size_bytes,
    )
    db.add(image)
    db.flush()  # asigna id sin cerrar la transaccion
    return image


def get_class_by_code(db: Session, code: str) -> LesionClass | None:
    return db.scalar(select(LesionClass).where(LesionClass.code == code))


def list_classes(db: Session) -> list[LesionClass]:
    return list(db.scalars(select(LesionClass).order_by(LesionClass.index)).all())


def map_classes_by_code(db: Session) -> dict[str, LesionClass]:
    return {row.code: row for row in list_classes(db)}


def get_model_by_version(db: Session, version: str) -> MLModel | None:
    return db.scalar(select(MLModel).where(MLModel.version == version))


def get_active_model(db: Session) -> MLModel | None:
    return db.scalar(select(MLModel).where(MLModel.is_active.is_(True)))


def ensure_model(db: Session, *, name: str, version: str, architecture: str) -> MLModel:
    """Devuelve el modelo pedido; lo registra si aun no existe (p. ej. un
    checkpoint nuevo cuya version no esta en el catalogo)."""
    model = get_model_by_version(db, version)
    if model is not None:
        return model

    model = MLModel(
        name=name,
        architecture=architecture,
        version=version,
        is_active=True,
    )
    db.add(model)
    db.flush()
    return model


def list_models(db: Session) -> list[MLModel]:
    return list(db.scalars(select(MLModel).order_by(MLModel.accuracy.desc())).all())
