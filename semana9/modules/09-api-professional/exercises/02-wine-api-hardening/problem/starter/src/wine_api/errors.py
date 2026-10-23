"""Errores de dominio y su traducción a un único sobre HTTP."""

import logging
from collections.abc import Sequence
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from wine_api.request_id import REQUEST_ID_HEADER, current_request_id
from wine_api.schemas import ErrorCode, ErrorDetail, ErrorResponse, FieldError

logger = logging.getLogger("wine_api")

HTTP_ERROR_CODES = {
    404: (ErrorCode.NOT_FOUND, "The requested resource does not exist"),
    405: (ErrorCode.METHOD_NOT_ALLOWED, "Method not allowed for this resource"),
}


class WineApiError(Exception):
    """Base de los errores que la API sabe explicar al consumidor."""

    status_code = 500
    code = ErrorCode.INTERNAL_ERROR
    message = "Unexpected server error"


class ModelUnavailableError(WineApiError):
    status_code = 503
    code = ErrorCode.MODEL_UNAVAILABLE
    message = "The prediction model is not ready"


def error_response(
    request: Request,
    status_code: int,
    code: ErrorCode,
    message: str,
    fields: list[FieldError] | None = None,
) -> JSONResponse:
    """Construye el sobre de error; `fields` desaparece si no aplica."""

    request_id = current_request_id(request)
    body = ErrorResponse(
        error=ErrorDetail(code=code, message=message, fields=fields),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json", exclude_none=True),
        headers={REQUEST_ID_HEADER: request_id},
    )


def field_path(loc: Sequence[Any]) -> str:
    """Convierte `("body", "features", "alcohol")` en `features.alcohol`."""

    parts = [str(part) for part in loc if part != "body"]
    return ".".join(parts) or "body"


async def handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # TODO S9.2a: FastAPI responde 422 con {"detail": [...]}, que no es nuestro
    # contrato. Recorre `exc.errors()`: cada error trae `type`, `loc` y `msg`.
    # - Si algún `type` es "json_invalid", el cuerpo no es JSON: 400 con
    #   `ErrorCode.INVALID_JSON` y sin `fields`.
    # - Si no, 422 con `ErrorCode.VALIDATION_ERROR` y una lista de FieldError
    #   (usa `field_path`). Nunca copies `input`: puede contener datos del
    #   usuario. Comprobación: tests/test_s9_2_errors.py
    raise NotImplementedError("TODO S9.2a")


async def handle_api_error(request: Request, exc: WineApiError) -> JSONResponse:
    # TODO S9.2b: traduce cualquier WineApiError usando los atributos de clase
    # `status_code`, `code` y `message`. Una línea con `error_response`.
    raise NotImplementedError("TODO S9.2b")


async def handle_http_exception(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    # TODO S9.2c: 404 y 405 los genera Starlette, no tus rutas. Busca el código
    # en HTTP_ERROR_CODES (ErrorCode.HTTP_ERROR si no está) y responde con el
    # mismo sobre. ¿Por qué se registra la clase de Starlette y no la de FastAPI?
    raise NotImplementedError("TODO S9.2c")


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    # TODO S9.2d: último recurso. Registra el detalle con `logger.exception`
    # (incluye el request_id) y devuelve 500 `internal_error` con un mensaje
    # genérico. El texto de `exc` nunca sale en la respuesta.
    raise NotImplementedError("TODO S9.2d")


def install_error_handlers(app: FastAPI) -> None:
    # TODO S9.2e: registra los cuatro manejadores con `app.add_exception_handler`
    # cuando estén implementados. Hasta entonces la API usa los errores por
    # defecto de FastAPI ({"detail": ...}), que es justo lo que queremos cambiar.
    return None
