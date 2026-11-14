"""Detalle de una prediccion y registro de feedback humano."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_optional
from app.db.session import get_db
from app.models.user import User
from app.repositories import catalog as catalog_repo
from app.repositories import predictions as predictions_repo
from app.schemas.feedback import FeedbackCreate, FeedbackRead
from app.schemas.prediction import PredictionDetailRead
from app.services.pdf_report import PDFReportService

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get(
    "/{prediction_id}/report.pdf",
    summary="Informe clinico en PDF (solo el propietario)",
    responses={200: {"content": {"application/pdf": {}}}},
)
def get_prediction_report(
    prediction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    prediction = predictions_repo.get_prediction(db, prediction_id)
    if prediction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prediccion no encontrada"
        )
    if prediction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a esta prediccion",
        )
    pdf = PDFReportService().generate(prediction, user_label=current_user.name)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="informe-{prediction.id}.pdf"'
        },
    )


@router.get(
    "/{prediction_id}",
    response_model=PredictionDetailRead,
    summary="Detalle de una prediccion",
)
def get_prediction(prediction_id: int, db: Session = Depends(get_db)):
    prediction = predictions_repo.get_prediction(db, prediction_id)
    if prediction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prediccion no encontrada"
        )
    return prediction


@router.post(
    "/{prediction_id}/feedback",
    response_model=FeedbackRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registra la revision humana de una prediccion",
)
def create_feedback(
    prediction_id: int,
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> FeedbackRead:
    prediction = predictions_repo.get_prediction(db, prediction_id)
    if prediction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prediccion no encontrada"
        )

    corrected_class = None
    if payload.corrected_label:
        corrected_class = catalog_repo.get_class_by_code(db, payload.corrected_label)
        if corrected_class is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Etiqueta desconocida: {payload.corrected_label}",
            )

    return predictions_repo.add_feedback(
        db,
        prediction=prediction,
        is_correct=payload.is_correct,
        corrected_class=corrected_class,
        comment=payload.comment,
        reviewer_id=current_user.id if current_user else None,
    )
