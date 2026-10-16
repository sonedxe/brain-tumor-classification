"""Catalogos: modelos registrados y clases de lesion."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import catalog as catalog_repo
from app.schemas.catalog import LesionClassRead, MLModelRead

router = APIRouter(tags=["catalog"])


@router.get("/models", response_model=list[MLModelRead], summary="Modelos registrados")
def list_models(db: Session = Depends(get_db)) -> list:
    """Las cinco arquitecturas comparadas, con su accuracy y numero de parametros."""
    return catalog_repo.list_models(db)


@router.get("/classes", response_model=list[LesionClassRead], summary="Catalogo de clases")
def list_classes(db: Session = Depends(get_db)) -> list:
    return catalog_repo.list_classes(db)
