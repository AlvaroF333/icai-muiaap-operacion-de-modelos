"""Demo S9 · Bloque 3 — Documentación que no miente.

Desde la raíz del módulo:

    uv run fastapi dev examples/openapi_demo.py

Abre /docs, /redoc y /openapi.json y localiza cada declaración de este archivo.
"""

from typing import Annotated

from fastapi import APIRouter, Body, FastAPI
from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    error: dict[str, str]


class ScoringRequest(BaseModel):
    """Solicitud de scoring de riesgo."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"age": 42, "income": 38000.0}]}
    )

    age: int = Field(ge=18, le=100, description="Edad en años cumplidos.")
    income: float = Field(gt=0, description="Ingresos anuales brutos en euros.")


class ScoringResponse(BaseModel):
    score: float = Field(ge=0, le=1, description="Probabilidad de impago.")
    model_version: str = Field(description="Versión del artefacto que ha inferido.")


router = APIRouter(
    prefix="/v1/scores",
    tags=["scoring"],
    responses={
        422: {"model": ErrorResponse, "description": "Entrada fuera de contrato."},
        503: {"model": ErrorResponse, "description": "Modelo no disponible."},
    },
)


@router.post(
    "",
    summary="Calcular el score de riesgo",
    response_description="Score y versión del modelo.",
)
def create_score(
    payload: Annotated[
        ScoringRequest,
        Body(
            openapi_examples={
                "valid": {
                    "summary": "Cliente válido",
                    "value": {"age": 42, "income": 38000},
                },
                "minor": {
                    "summary": "Menor de edad: 422",
                    "value": {"age": 16, "income": 1},
                },
            }
        ),
    ],
) -> ScoringResponse:
    """Calcula la probabilidad de impago de un cliente.

    - `age` entre 18 y 100, `income` mayor que 0.
    - El score es docente: **no** es una decisión de crédito.
    """

    return ScoringResponse(
        score=round(min(1.0, 10_000 / payload.income), 2), model_version="1.4.2"
    )


app = FastAPI(
    title="Demo S9 · OpenAPI",
    version="1.0.0",
    summary="Scoring de riesgo documentado.",
    description="Todas las respuestas de error usan `ErrorResponse`.",
    openapi_tags=[{"name": "scoring", "description": "Inferencia de riesgo."}],
)
app.include_router(router)
