"""Contratos de entrada y salida entregados desde la semana 3."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat

QualityBand = Literal["needs_review", "acceptable", "excellent"]


class WineQualityRequest(BaseModel):
    """Mediciones físico-químicas de una muestra de vino tinto."""

    model_config = ConfigDict(extra="forbid")

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


class WineQualityPrediction(BaseModel):
    """Respuesta con la identidad del bundle que la generó."""

    model_config = ConfigDict(extra="forbid")

    quality_band: QualityBand
    confidence: FiniteFloat = Field(ge=0, le=1)
    model_version: str = Field(min_length=1)
    preprocessing_version: str = Field(min_length=1)
