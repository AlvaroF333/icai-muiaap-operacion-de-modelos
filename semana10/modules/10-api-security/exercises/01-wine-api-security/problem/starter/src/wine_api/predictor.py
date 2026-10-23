"""Predictores intercambiables detrás de un protocolo.

En el proyecto, `DemoWinePredictor` se sustituye por un adaptador que carga el
bundle de S4. La API solo depende del protocolo `Predictor`.
"""

from dataclasses import dataclass
from typing import Protocol

from wine_api.errors import ModelUnavailableError
from wine_api.schemas import QualityBand, WineFeatures

MODEL_VERSION = "wine-quality-demo-v1"
PREPROCESSING_VERSION = "wine-red-features-v1"


@dataclass(frozen=True)
class ModelOutput:
    """Salida interna del modelo; `raw_score` nunca sale por la API."""

    quality_band: QualityBand
    confidence: float
    raw_score: float
    model_version: str
    preprocessing_version: str


class Predictor(Protocol):
    model_version: str

    def is_ready(self) -> bool: ...

    def predict(self, features: WineFeatures) -> ModelOutput: ...


@dataclass(frozen=True)
class DemoWinePredictor:
    """Predicción determinista para practicar el contrato, no para negocio."""

    model_version: str = MODEL_VERSION
    preprocessing_version: str = PREPROCESSING_VERSION

    def is_ready(self) -> bool:
        return True

    def predict(self, features: WineFeatures) -> ModelOutput:
        score = (
            5.5
            + 0.25 * (features.alcohol - 10.0)
            - 1.2 * (features.volatile_acidity - 0.5)
            + 0.4 * (features.sulphates - 0.6)
        )
        if score < 5.5:
            band = QualityBand.NEEDS_REVIEW
        elif score < 6.5:
            band = QualityBand.ACCEPTABLE
        else:
            band = QualityBand.EXCELLENT
        confidence = min(0.95, 0.60 + abs(score - 6.0) * 0.12)
        return ModelOutput(
            quality_band=band,
            confidence=confidence,
            raw_score=score,
            model_version=self.model_version,
            preprocessing_version=self.preprocessing_version,
        )


@dataclass(frozen=True)
class UnavailablePredictor:
    """Simula un artefacto que no se ha podido cargar."""

    model_version: str = MODEL_VERSION

    def is_ready(self) -> bool:
        return False

    def predict(self, features: WineFeatures) -> ModelOutput:
        raise ModelUnavailableError()


def build_predictor(mode: str) -> Predictor:
    """Elige el predictor según `Settings.mode` (`WINE_API_MODE`)."""

    if mode == "unavailable":
        return UnavailablePredictor()
    return DemoWinePredictor()
