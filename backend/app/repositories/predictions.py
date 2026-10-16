"""Repositorio de predicciones: creacion, consulta, feedback y estadisticas."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.feedback import PredictionFeedback
from app.models.image import Image
from app.models.lesion_class import LesionClass
from app.models.ml_model import MLModel
from app.models.prediction import Prediction, PredictionScore


def create_prediction(
    db: Session,
    *,
    image: Image,
    model: MLModel,
    predicted_class: LesionClass,
    confidence: float,
    inference_ms: float,
    gradcam_path: str | None,
    scores: list[tuple[LesionClass, float]],
    user_id: int | None = None,
    source: str = "api",
) -> Prediction:
    prediction = Prediction(
        image_id=image.id,
        model_id=model.id,
        predicted_class_id=predicted_class.id,
        user_id=user_id,
        confidence=confidence,
        inference_ms=inference_ms,
        gradcam_path=gradcam_path,
        source=source,
    )
    prediction.scores = [
        PredictionScore(class_id=lesion_class.id, probability=float(probability))
        for lesion_class, probability in scores
    ]
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction


def list_predictions(db: Session, *, limit: int = 20, offset: int = 0) -> list[Prediction]:
    stmt = (
        select(Prediction)
        .options(
            selectinload(Prediction.image),
            selectinload(Prediction.model),
            selectinload(Prediction.predicted_class),
        )
        .order_by(Prediction.created_at.desc(), Prediction.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(stmt).all())


def get_prediction(db: Session, prediction_id: int) -> Prediction | None:
    stmt = (
        select(Prediction)
        .where(Prediction.id == prediction_id)
        .options(
            selectinload(Prediction.image),
            selectinload(Prediction.model),
            selectinload(Prediction.predicted_class),
            selectinload(Prediction.scores).selectinload(PredictionScore.lesion_class),
            selectinload(Prediction.feedback).selectinload(
                PredictionFeedback.corrected_class
            ),
        )
    )
    return db.scalar(stmt)


def add_feedback(
    db: Session,
    *,
    prediction: Prediction,
    is_correct: bool,
    corrected_class: LesionClass | None = None,
    comment: str | None = None,
    reviewer_id: int | None = None,
) -> PredictionFeedback:
    feedback = PredictionFeedback(
        prediction_id=prediction.id,
        reviewer_id=reviewer_id,
        is_correct=is_correct,
        corrected_class_id=corrected_class.id if corrected_class else None,
        comment=comment,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def stats_summary(db: Session) -> dict:
    total = db.scalar(select(func.count()).select_from(Prediction)) or 0
    unique_images = db.scalar(select(func.count()).select_from(Image)) or 0
    models_registered = db.scalar(select(func.count()).select_from(MLModel)) or 0
    total_feedback = db.scalar(select(func.count()).select_from(PredictionFeedback)) or 0

    avg_confidence = db.scalar(select(func.avg(Prediction.confidence)))
    avg_inference_ms = db.scalar(select(func.avg(Prediction.inference_ms)))

    rows = db.execute(
        select(
            LesionClass.code,
            LesionClass.display_name,
            func.count(Prediction.id),
            func.avg(Prediction.confidence),
        )
        .join(Prediction, Prediction.predicted_class_id == LesionClass.id)
        .group_by(LesionClass.code, LesionClass.display_name)
        .order_by(func.count(Prediction.id).desc())
    ).all()

    return {
        "total_predictions": int(total),
        "unique_images": int(unique_images),
        "models_registered": int(models_registered),
        "total_feedback": int(total_feedback),
        "avg_confidence": float(avg_confidence) if avg_confidence is not None else None,
        "avg_inference_ms": float(avg_inference_ms) if avg_inference_ms is not None else None,
        "by_class": [
            {
                "code": code,
                "display_name": display_name,
                "count": int(count),
                "avg_confidence": float(avg) if avg is not None else None,
            }
            for code, display_name, count, avg in rows
        ],
    }
