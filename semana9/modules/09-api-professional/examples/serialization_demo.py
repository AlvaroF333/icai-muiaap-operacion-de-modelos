"""Demo S9 · Bloque 1 — La respuesta también es un contrato.

Desde la raíz del módulo:

    uv run fastapi dev examples/serialization_demo.py

Compara en /docs los esquemas de respuesta de cada endpoint.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field, computed_field, field_serializer

app = FastAPI(title="Demo S9 · Serialización", version="0.1.0")


class Band(StrEnum):
    NEEDS_REVIEW = "needs_review"
    ACCEPTABLE = "acceptable"
    EXCELLENT = "excellent"


class InternalScore(BaseModel):
    """Lo que produce el modelo: incluye datos que no son del consumidor."""

    band: Band
    confidence: float
    raw_score: float
    threshold_config: str


class PublicScore(BaseModel):
    """Lo que promete la API."""

    band: Band
    confidence: float = Field(ge=0, le=1)
    served_at: datetime
    note: str | None = None

    @field_serializer("confidence")
    def _two_decimals(self, value: float) -> float:
        return round(value, 2)

    @field_serializer("served_at")
    def _utc_z(self, value: datetime) -> str:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")

    @computed_field
    @property
    def is_reliable(self) -> bool:
        return self.confidence >= 0.8


def run_model() -> InternalScore:
    return InternalScore(
        band=Band.ACCEPTABLE,
        confidence=0.8312377,
        raw_score=6.137,
        threshold_config="/srv/models/thresholds.yaml",
    )


@app.get("/v1/scores/leaky")
def read_leaky_score() -> dict[str, Any]:
    """Antipatrón: devuelvo un dict y se escapa todo lo interno."""

    return run_model().model_dump()


@app.get("/v1/scores/public")
def read_public_score() -> PublicScore:
    """Return type: FastAPI valida, filtra, documenta y serializa."""

    score = run_model()
    return PublicScore(
        band=score.band, confidence=score.confidence, served_at=datetime.now(UTC)
    )


@app.get("/v1/scores/filtered", response_model=PublicScore)
def read_filtered_score() -> Any:
    """`response_model` cuando devuelvo otro tipo: filtra lo que no declara."""

    return {**run_model().model_dump(), "served_at": datetime.now(UTC)}


@app.get(
    "/v1/scores/compact",
    response_model=PublicScore,
    response_model_exclude_none=True,
)
def read_compact_score() -> Any:
    """`note` es None: con `exclude_none` el campo no aparece."""

    return {**run_model().model_dump(), "served_at": datetime.now(UTC)}
