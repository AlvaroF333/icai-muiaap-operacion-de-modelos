"""Autenticación por API key y autorización por scopes.

- Autenticación (401): ¿quién llama? La clave de `X-API-Key` debe coincidir con
  la de algún cliente configurado.
- Autorización (403): ¿qué puede hacer? El cliente debe tener el scope que
  exige el router.

La clave nunca se devuelve ni se registra en los logs.
"""

import logging
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Security
from fastapi.security import APIKeyHeader

from wine_api.dependencies import RequestIdDep, SettingsDep
from wine_api.errors import AuthenticationError, PermissionDeniedError
from wine_api.schemas import ErrorResponse
from wine_api.settings import Scope

logger = logging.getLogger("wine_api.security")

API_KEY_HEADER = "X-API-Key"

api_key_header = APIKeyHeader(
    name=API_KEY_HEADER,
    auto_error=False,
    description="API key del cliente. La entrega el equipo de operación.",
)

AUTH_RESPONSES: dict[int | str, dict] = {
    401: {
        "model": ErrorResponse,
        "description": "Falta la cabecera `X-API-Key` o la clave no es válida.",
    },
    403: {
        "model": ErrorResponse,
        "description": "La clave es válida, pero no tiene el scope necesario.",
    },
}


@dataclass(frozen=True)
class AuthenticatedClient:
    """Cliente ya autenticado. No guarda la clave: no la necesita nadie más."""

    name: str
    scopes: frozenset[str]
    rate_limit_per_minute: int


def authenticate_client(
    settings: SettingsDep,
    request_id: RequestIdDep,
    api_key: Annotated[str | None, Security(api_key_header)],
) -> AuthenticatedClient:
    """Identifica al cliente por su API key o lanza `AuthenticationError`."""

    if api_key:
        # Bytes, no `str`: `compare_digest` rechaza `str` con caracteres no ASCII.
        candidate = api_key.encode()
        for name, client in settings.clients.items():
            expected = client.key.get_secret_value().encode()
            if secrets.compare_digest(candidate, expected):
                return AuthenticatedClient(
                    name=name,
                    scopes=frozenset(client.scopes),
                    rate_limit_per_minute=client.rate_limit_per_minute,
                )
    # Se registra el intento, nunca la clave recibida.
    logger.warning(
        "Rejected request without a valid API key",
        extra={"request_id": request_id, "api_key_present": bool(api_key)},
    )
    raise AuthenticationError()


ClientDep = Annotated[AuthenticatedClient, Security(authenticate_client)]


def require_scope(scope: Scope) -> Callable[..., AuthenticatedClient]:
    """Crea una dependencia que exige `scope`; se declara en el `APIRouter`."""

    def check_scope(client: ClientDep) -> AuthenticatedClient:
        if scope not in client.scopes:
            logger.warning(
                "Client %s lacks scope %s", client.name, scope, extra={"scope": scope}
            )
            raise PermissionDeniedError()
        return client

    return check_scope
