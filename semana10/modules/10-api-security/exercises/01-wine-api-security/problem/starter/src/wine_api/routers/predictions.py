from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Body, Depends

from wine_api.dependencies import PredictorDep, RequestIdDep
from wine_api.rate_limit import RATE_LIMIT_RESPONSES, enforce_rate_limit
from wine_api.schemas import (
    VALID_FEATURES_EXAMPLE,
    ErrorResponse,
    Prediction,
    PredictionRequest,
    PredictionResponse,
)
from wine_api.security import AUTH_RESPONSES, require_scope

PREDICTION_EXAMPLES = {
    "valid": {
        "summary": "Vino válido",
        "description": "Devuelve `200` con la predicción.",
        "value": {"features": VALID_FEATURES_EXAMPLE},
    },
    "wrong_type": {
        "summary": "Tipo incorrecto",
        "description": "`alcohol` es un texto: devuelve `422`.",
        "value": {"features": {**VALID_FEATURES_EXAMPLE, "alcohol": "mucho"}},
    },
    "out_of_range": {
        "summary": "Fuera de rango",
        "description": "`ph` supera 4.5: devuelve `422`.",
        "value": {"features": {**VALID_FEATURES_EXAMPLE, "ph": 7.0}},
    },
}

# Orden: autenticar y autorizar (scope `predict`) y después contar la cuota.
router = APIRouter(
    prefix="/v1/predictions",
    tags=["predictions"],
    dependencies=[Depends(require_scope("predict")), Depends(enforce_rate_limit)],
    responses={
        400: {"model": ErrorResponse, "description": "El cuerpo no es JSON válido."},
        **AUTH_RESPONSES,
        422: {
            "model": ErrorResponse,
            "description": "JSON válido que incumple campos, tipos o rangos.",
        },
        **RATE_LIMIT_RESPONSES,
        503: {"model": ErrorResponse, "description": "El modelo no está cargado."},
    },
)


@router.post(
    "",
    summary="Predecir la banda de calidad de un vino",
    response_description="Predicción con versión del modelo y `request_id`.",
)
def create_prediction(
    payload: Annotated[PredictionRequest, Body(openapi_examples=PREDICTION_EXAMPLES)],
    predictor: PredictorDep,
    request_id: RequestIdDep,
) -> PredictionResponse:
    """Estima la banda de calidad a partir de once variables fisicoquímicas.

    - Requiere la cabecera `X-API-Key` de un cliente con scope `predict`.
    - Cada cliente tiene una cuota por minuto; las respuestas `200` indican lo
      que queda en `X-RateLimit-Remaining` y los `429` cuánto esperar en
      `Retry-After`.
    - Todos los campos son obligatorios y numéricos; no se aceptan booleanos,
      textos ni campos extra.
    - Los rangos son inclusivos y están en el esquema `WineFeatures`.
    - `confidence` se devuelve con dos decimales.
    - Guarda `request_id` si necesitas reportar una incidencia.
    """

    output = predictor.predict(payload.features)
    return PredictionResponse(
        prediction=Prediction.model_validate(output, from_attributes=True),
        request_id=request_id,
        served_at=datetime.now(UTC),
    )
