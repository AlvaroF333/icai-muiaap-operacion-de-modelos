"""Demo S9 · Bloque 2 — Fallar de forma predecible.

Desde la raíz del módulo:

    uv run fastapi dev examples/errors_demo.py

Prueba en /docs un cuerpo válido, uno con `age: "treinta"`, una ruta que no
existe y `GET /v1/boom`. Todas las respuestas de error tienen la misma forma.
"""

import logging
from typing import Annotated

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("errors_demo")

app = FastAPI(title="Demo S9 · Errores", version="0.1.0")


class ScoringRequest(BaseModel):
    age: int = Field(ge=18, le=100)
    income: float = Field(gt=0)


class ScoringResponse(BaseModel):
    score: float


class ModelUnavailableError(Exception):
    """Error de dominio: no sabe nada de HTTP."""


class Model:
    ready = True

    def predict(self, request: ScoringRequest) -> float:
        if not self.ready:
            raise ModelUnavailableError()
        return round(min(1.0, request.income / 100_000), 2)


def get_model() -> Model:
    return Model()


ModelDep = Annotated[Model, Depends(get_model)]


def error_body(code: str, message: str, fields: list | None = None) -> dict:
    error: dict = {"code": code, "message": message}
    if fields is not None:
        error["fields"] = fields
    return {"error": error}


@app.exception_handler(ModelUnavailableError)
async def handle_model_unavailable(
    request: Request, exc: ModelUnavailableError
) -> JSONResponse:
    return JSONResponse(
        status_code=503, content=error_body("model_unavailable", "Model not ready")
    )


@app.exception_handler(RequestValidationError)
async def handle_validation(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    fields = [
        {
            "field": ".".join(str(p) for p in err["loc"] if p != "body"),
            "message": err["msg"],
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=error_body("validation_error", "Invalid input", fields),
    )


@app.exception_handler(StarletteHTTPException)
async def handle_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = "not_found" if exc.status_code == 404 else "http_error"
    return JSONResponse(
        status_code=exc.status_code, content=error_body(code, "HTTP error")
    )


@app.exception_handler(Exception)
async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error")  # el detalle se queda en el servidor
    return JSONResponse(
        status_code=500, content=error_body("internal_error", "Unexpected error")
    )


@app.post("/v1/scores")
def create_score(payload: ScoringRequest, model: ModelDep) -> ScoringResponse:
    return ScoringResponse(score=model.predict(payload))


@app.get("/v1/boom")
def explode() -> dict:
    raise RuntimeError("password=TU_SECRETO in /etc/app.conf")
