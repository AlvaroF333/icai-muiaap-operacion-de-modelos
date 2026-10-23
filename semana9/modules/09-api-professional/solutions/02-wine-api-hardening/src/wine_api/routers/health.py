from fastapi import APIRouter

from wine_api.dependencies import PredictorDep, RequestIdDep
from wine_api.errors import ModelUnavailableError
from wine_api.schemas import ErrorResponse, HealthResponse

SERVICE_NAME = "wine-quality-prediction"

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Comprobar que el servicio puede predecir",
    response_description="El servicio y el modelo están listos.",
    responses={
        503: {"model": ErrorResponse, "description": "El modelo no está cargado."},
    },
)
def read_health(predictor: PredictorDep, request_id: RequestIdDep) -> HealthResponse:
    """Devuelve el estado del servicio y la versión del modelo cargado.

    Úsalo como *readiness probe*: un `200` significa que `POST /v1/predictions`
    puede responder; un `503` con `model_unavailable`, que el artefacto no está
    disponible y el cliente debe reintentar más tarde.
    """

    if not predictor.is_ready():
        raise ModelUnavailableError()
    return HealthResponse(
        status="ok",
        service=SERVICE_NAME,
        model_status="ready",
        model_version=predictor.model_version,
        request_id=request_id,
    )
