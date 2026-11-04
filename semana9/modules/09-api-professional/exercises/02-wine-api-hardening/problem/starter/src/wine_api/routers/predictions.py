from datetime import UTC, datetime

from fastapi import APIRouter

from wine_api.dependencies import PredictorDep, RequestIdDep
from wine_api.schemas import Prediction, PredictionRequest, PredictionResponse

# TODO S9.3a: mueve aquí `prefix="/v1/predictions"` y `tags=["predictions"]`.
# TODO S9.3c: declara a nivel de router `responses=` para 400, 422 y 503 con
# `{"model": ErrorResponse, "description": ...}`. Así el 422 deja de
# documentarse como `HTTPValidationError`, que ya no es lo que devolvemos.
router = APIRouter()


@router.post("/v1/predictions")
def create_prediction(
    payload: PredictionRequest,
    predictor: PredictorDep,
    request_id: RequestIdDep,
) -> PredictionResponse:
    # TODO S9.3e: añade summary, response_description y un docstring útil para
    # quien consume la API (campos, rangos, decimales de confidence).
    # TODO S9.3f: ofrece en Swagger al menos tres ejemplos de cuerpo (uno válido
    # y dos inválidos). Investiga `Annotated[PredictionRequest, Body(...)]` con
    # `openapi_examples=`; usa VALID_FEATURES_EXAMPLE como base.
    output = predictor.predict(payload.features)
    # S9.1e: construye PredictionResponse con from_attributes para Prediction.
    return PredictionResponse(
        prediction=Prediction.model_validate(output, from_attributes=True),
        request_id=request_id,
        served_at=datetime.now(UTC),
    )
