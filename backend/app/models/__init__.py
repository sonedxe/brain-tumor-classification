"""Modelos SQLAlchemy del backend.

Importar todos los modelos aqui garantiza que `Base.metadata` conozca todas las
tablas antes de `create_all`, tanto en la app como en las pruebas.
"""

from __future__ import annotations

from app.models.auth_session import AuthSession
from app.models.feedback import PredictionFeedback
from app.models.image import Image
from app.models.lesion_class import LesionClass
from app.models.ml_model import MLModel
from app.models.prediction import Prediction, PredictionScore
from app.models.user import User

__all__ = [
    "AuthSession",
    "Image",
    "LesionClass",
    "MLModel",
    "Prediction",
    "PredictionFeedback",
    "PredictionScore",
    "User",
]
