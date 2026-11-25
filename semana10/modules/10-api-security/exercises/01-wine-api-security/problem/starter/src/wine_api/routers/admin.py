from fastapi import APIRouter, Depends

from wine_api.dependencies import RequestIdDep, SettingsDep
from wine_api.rate_limit import RateLimiterDep
from wine_api.schemas import ClientUsage, UsageResponse
from wine_api.security import AUTH_RESPONSES, require_scope

router = APIRouter(
    prefix="/v1/admin",
    tags=["admin"],
    dependencies=[Depends(require_scope("admin"))],
    responses=AUTH_RESPONSES,
)


@router.get(
    "/usage",
    summary="Consultar el consumo de cada cliente",
    response_description="Peticiones de cada cliente en la ventana actual.",
)
def read_usage(
    settings: SettingsDep, limiter: RateLimiterDep, request_id: RequestIdDep
) -> UsageResponse:
    """Devuelve, por cliente, cuántas predicciones lleva en la ventana actual.

    - Requiere la cabecera `X-API-Key` de un cliente con scope `admin`.
    - Identifica a los clientes por su nombre; las claves nunca se devuelven.
    - El contador es del proceso que responde: con varias réplicas, cada una
      informa de lo suyo.
    """

    clients = [
        ClientUsage(
            client=name,
            requests_in_window=limiter.usage(name),
            limit=config.rate_limit_per_minute,
        )
        for name, config in sorted(settings.clients.items())
    ]
    return UsageResponse(clients=clients, request_id=request_id)
