"""Identificador por petición, compartido por respuestas, errores y logs."""

import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response

REQUEST_ID_HEADER = "X-Request-Id"


def new_request_id() -> str:
    """Crea un identificador opaco y corto."""

    return f"req_{uuid.uuid4().hex[:12]}"


def current_request_id(request: Request) -> str:
    """Devuelve el ID de la petición o crea uno si el middleware no llegó a correr."""

    request_id = getattr(request.state, "request_id", None)
    if request_id is None:
        request_id = new_request_id()
        request.state.request_id = request_id
    return request_id


async def request_id_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Asigna el ID antes de la ruta y lo devuelve en la cabecera."""

    request_id = current_request_id(request)
    response = await call_next(request)
    response.headers[REQUEST_ID_HEADER] = request_id
    return response
