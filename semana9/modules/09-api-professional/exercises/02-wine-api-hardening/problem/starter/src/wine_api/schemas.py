"""Contratos públicos de la Wine Quality API.

Punto de partida: la API de S8 valida la entrada, pero la salida todavía es un
`dict` sin contrato. En S9 la respuesta también pasa a ser un contrato.
"""

from datetime import UTC, datetime  # noqa: F401 - pista para el TODO S9.1c
from enum import StrEnum
from typing import Literal

from pydantic import (  # noqa: F401 - pistas para S9.1
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
)

VALID_FEATURES_EXAMPLE = {
    "fixed_acidity": 7.4,
    "volatile_acidity": 0.7,
    "citric_acid": 0.0,
    "residual_sugar": 1.9,
    "chlorides": 0.076,
    "free_sulfur_dioxide": 11.0,
    "total_sulfur_dioxide": 34.0,
    "density": 0.9978,
    "ph": 3.51,
    "sulphates": 0.56,
    "alcohol": 9.4,
}


class WineFeatures(BaseModel):
    """Once variables fisicoquímicas de un vino tinto, con rangos inclusivos."""

    model_config = ConfigDict(extra="forbid", strict=True)

    # TODO S9.3d: añade `description=` a cada Field (unidad incluida, p. ej.
    # "Alcohol (% vol.)."). Swagger la muestra junto al rango; el test
    # `test_feature_fields_are_described` comprueba los once campos.
    fixed_acidity: float = Field(ge=0, le=20)
    volatile_acidity: float = Field(ge=0, le=2)
    citric_acid: float = Field(ge=0, le=2)
    residual_sugar: float = Field(ge=0, le=20)
    chlorides: float = Field(ge=0, le=1)
    free_sulfur_dioxide: float = Field(ge=0, le=100)
    total_sulfur_dioxide: float = Field(ge=0, le=300)
    density: float = Field(ge=0.98, le=1.01)
    ph: float = Field(ge=2.5, le=4.5)
    sulphates: float = Field(ge=0, le=3)
    alcohol: float = Field(ge=5, le=20)


class PredictionRequest(BaseModel):
    """Cuerpo de `POST /v1/predictions`."""

    model_config = ConfigDict(extra="forbid")

    features: WineFeatures


class QualityBand(StrEnum):
    """Bandas de calidad que entiende el consumidor."""

    NEEDS_REVIEW = "needs_review"
    ACCEPTABLE = "acceptable"
    EXCELLENT = "excellent"


class Prediction(BaseModel):
    """Predicción pública: no incluye puntuaciones internas del modelo."""

    # TODO S9.1a: declara los cuatro campos públicos del contrato de S7:
    # `quality_band` (usa QualityBand, no `str`), `confidence` (entre 0 y 1),
    # `model_version` y `preprocessing_version`. Lo que no declares aquí no
    # saldrá en la respuesta: así se filtra `raw_score`.
    # TODO S9.1b: el modelo devuelve la confianza con todos sus decimales; el
    # contrato público la expone con dos. Investiga `@field_serializer` de
    # Pydantic v2: la decisión pertenece al contrato, no al predictor.
    # Comprobación: tests/test_s9_1_output_contract.py


class PredictionResponse(BaseModel):
    """Respuesta de `POST /v1/predictions`."""

    # TODO S9.1c: declara `prediction: Prediction`, `request_id: str` y un campo
    # nuevo `served_at: datetime`. Serialízalo en UTC, ISO 8601 y con sufijo
    # `Z` (por ejemplo `2026-10-20T09:15:00.123Z`). Añadir un campo es un
    # cambio compatible: ¿qué parte de la versión de la API debes subir?


class HealthResponse(BaseModel):
    """Estado del servicio y del modelo cargado."""

    status: Literal["ok"]
    service: str
    model_status: Literal["ready"]
    model_version: str
    request_id: str


class ErrorCode(StrEnum):
    """Códigos estables: el cliente programa contra ellos, no contra el texto."""

    INVALID_JSON = "invalid_json"
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    METHOD_NOT_ALLOWED = "method_not_allowed"
    HTTP_ERROR = "http_error"
    MODEL_UNAVAILABLE = "model_unavailable"
    INTERNAL_ERROR = "internal_error"


class FieldError(BaseModel):
    """Un campo del cuerpo que incumple el contrato."""

    field: str = Field(examples=["features.alcohol"])
    message: str = Field(examples=["Input should be a valid number"])


class ErrorDetail(BaseModel):
    """Descripción estable del error."""

    code: ErrorCode
    message: str
    fields: list[FieldError] | None = Field(
        default=None, description="Solo presente en errores de validación."
    )


class ErrorResponse(BaseModel):
    """Sobre común de todas las respuestas de error (contrato de S7)."""

    error: ErrorDetail
    request_id: str
