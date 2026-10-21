"""Puntos de extensión del taller de serialización."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol, cast

import joblib
from pydantic import BaseModel, ConfigDict, Field, field_validator

from model_packaging.contracts import (
    QualityBand,
    WineQualityPrediction,
    WineQualityRequest,
)
from model_packaging.preprocess import (
    FEATURE_NAMES,
    PREPROCESSING_VERSION,
    preprocess_wine_request,
)

ARTIFACT_SCHEMA_VERSION = "wine-quality-bundle-v1"
DEFAULT_BUNDLE_PATH = Path("models/wine_quality_bundle")
MANIFEST_FILENAME = "manifest.json"
MODEL_FILENAME = "model.joblib"
OUTPUT_LABELS: tuple[QualityBand, ...] = (
    "needs_review",
    "acceptable",
    "excellent",
)


class WineQualityEstimator(Protocol):
    """Interfaz mínima que debe cumplir el estimador cargado."""

    def predict(self, features: list[list[float]]) -> Sequence[str]:
        """Devuelve una etiqueta por fila."""

    def predict_proba(self, features: list[list[float]]) -> Sequence[Sequence[float]]:
        """Devuelve probabilidades por fila."""


class ArtifactManifest(BaseModel):
    """Declara y valida los metadatos del bundle."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str
    model_version: str = Field(min_length=1)
    preprocessing_version: str
    feature_names: tuple[str, ...]
    output_labels: tuple[QualityBand, ...]
    estimator_type: str = Field(min_length=1)

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        """Impide cargar una estructura de manifiesto desconocida."""
        if value != ARTIFACT_SCHEMA_VERSION:
            raise ValueError(
                f"schema_version incompatible: se esperaba {ARTIFACT_SCHEMA_VERSION}"
            )
        return value

    @field_validator("preprocessing_version")
    @classmethod
    def validate_preprocessing_version(cls, value: str) -> str:
        """Relaciona el manifiesto con el preprocesado de la semana 3."""
        if value != PREPROCESSING_VERSION:
            raise ValueError(
                "preprocessing_version incompatible: "
                f"se esperaba {PREPROCESSING_VERSION}"
            )
        return value

    @field_validator("feature_names")
    @classmethod
    def validate_feature_names(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        """Protege el orden de las once columnas del vector."""
        if tuple(value) != FEATURE_NAMES:
            raise ValueError("feature_names no coincide con el orden del contrato.")
        return value

    @field_validator("output_labels")
    @classmethod
    def validate_output_labels(
        cls, value: tuple[QualityBand, ...]
    ) -> tuple[QualityBand, ...]:
        """Fija las categorías que puede exponer la respuesta."""
        if tuple(value) != OUTPUT_LABELS:
            raise ValueError("output_labels no coincide con las categorías válidas.")
        return value

    @field_validator("model_version")
    @classmethod
    def validate_model_version(cls, value: str) -> str:
        """Evita versiones vacías o formadas solo por espacios."""
        if not value.strip():
            raise ValueError("model_version no puede estar vacío.")
        return value


@dataclass(frozen=True)
class LoadedModelBundle:
    """Bundle cargado; no modificar esta interfaz pública."""

    estimator: WineQualityEstimator
    manifest: ArtifactManifest


def _require_estimator(estimator: Any) -> WineQualityEstimator:
    """Comprueba la interfaz pública mínima antes de guardar o inferir."""
    if not callable(getattr(estimator, "predict", None)) or not callable(
        getattr(estimator, "predict_proba", None)
    ):
        raise ValueError("El estimador debe exponer predict y predict_proba.")
    return cast(WineQualityEstimator, estimator)


def create_manifest(
    estimator: WineQualityEstimator, model_version: str
) -> ArtifactManifest:
    """Devuelve un manifiesto (manifest) compatible con el contrato."""
    _require_estimator(estimator)
    return ArtifactManifest(
        schema_version=ARTIFACT_SCHEMA_VERSION,
        model_version=model_version,
        preprocessing_version=PREPROCESSING_VERSION,
        feature_names=FEATURE_NAMES,
        output_labels=OUTPUT_LABELS,
        estimator_type=type(estimator).__name__,
    )


def save_model_bundle(
    bundle_path: Path,
    estimator: WineQualityEstimator,
    manifest: ArtifactManifest | None = None,
) -> ArtifactManifest:
    """Escribe manifest.json y model.joblib de forma segura."""
    bundle_path.mkdir(parents=True, exist_ok=True)

    validated_estimator = _require_estimator(estimator)
    if manifest is None:
        manifest = create_manifest(validated_estimator, model_version="default-v1")
    else:
        _require_estimator(estimator)

    manifest_path = bundle_path / MANIFEST_FILENAME
    manifest_path.write_text(
        manifest.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )

    model_path = bundle_path / MODEL_FILENAME
    joblib.dump(validated_estimator, model_path)

    return manifest


def load_model_bundle(bundle_path: Path) -> LoadedModelBundle:
    """Valida el manifiesto antes de cargar el estimador."""
    manifest_path = bundle_path / MANIFEST_FILENAME
    if not manifest_path.exists():
        raise ValueError(f"No se encuentra el manifiesto en {bundle_path}")

    try:
        manifest = ArtifactManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
    except Exception as error:
        raise ValueError(f"Manifiesto inválido en {bundle_path}: {error}") from error

    # Invariante: si cambia el orden de las columnas, la inferencia no es válida
    if manifest.feature_names != FEATURE_NAMES:
        raise ValueError(
            "El orden de las variables del manifiesto es incompatible con el "
            "preprocesado actual."
        )

    model_path = bundle_path / MODEL_FILENAME
    if not model_path.exists():
        raise ValueError(f"No se encuentra el estimador en {bundle_path}")

    payload = joblib.load(model_path)
    if isinstance(payload, dict) and "estimator" in payload:
        estimator = payload["estimator"]
    else:
        estimator = payload

    validated_estimator = _require_estimator(estimator)

    return LoadedModelBundle(estimator=validated_estimator, manifest=manifest)


def infer_wine_quality(
    bundle: LoadedModelBundle,
    request: WineQualityRequest,
) -> WineQualityPrediction:
    """Preprocesa, invoca el estimador y valida la respuesta."""
    features = preprocess_wine_request(request).as_vector()

    predicted_labels = bundle.estimator.predict([features])
    if len(predicted_labels) != 1:
        raise ValueError("El estimador debe devolver una salida por fila.")
    prediction_label = str(predicted_labels[0])

    # Invariante de salida: bloquear etiquetas fuera de contrato
    if prediction_label not in bundle.manifest.output_labels:
        raise ValueError(
            f"Etiqueta de inferencia desconocida o no permitida: {prediction_label}"
        )

    probabilities = bundle.estimator.predict_proba([features])
    if len(probabilities) != 1 or len(probabilities[0]) == 0:
        raise ValueError("El estimador debe devolver probabilidades válidas.")
    confidence = max(float(val) for val in probabilities[0])

    return WineQualityPrediction(
        quality_band=prediction_label,  # type: ignore[arg-type]
        confidence=confidence,
        model_version=bundle.manifest.model_version,
        preprocessing_version=bundle.manifest.preprocessing_version,
    )
