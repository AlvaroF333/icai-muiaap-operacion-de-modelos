"""Puntos de extensión del taller de serialización."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import joblib
from pydantic import BaseModel, ConfigDict, Field

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


@dataclass(frozen=True)
class LoadedModelBundle:
    """Bundle cargado; no modificar esta interfaz pública."""

    estimator: WineQualityEstimator
    manifest: ArtifactManifest


def create_manifest(
    estimator: WineQualityEstimator, model_version: str
) -> ArtifactManifest:
    """Devuelve un manifiesto compatible con el contrato."""
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

    if manifest is None:
        manifest = create_manifest(estimator, model_version="default-v1")

    manifest_path = bundle_path / MANIFEST_FILENAME
    manifest_path.write_text(manifest.model_dump_json(indent=2))

    model_path = bundle_path / MODEL_FILENAME
    joblib.dump(estimator, model_path)

    return manifest


def load_model_bundle(bundle_path: Path) -> LoadedModelBundle:
    """Valida el manifiesto antes de cargar el estimador."""
    manifest_path = bundle_path / MANIFEST_FILENAME
    if not manifest_path.exists():
        raise ValueError(f"No se encuentra el manifiesto en {bundle_path}")

    manifest = ArtifactManifest.model_validate_json(manifest_path.read_text())

    # Invariante: si cambia el orden de las columnas, la inferencia no es válida
    if manifest.feature_names != FEATURE_NAMES:
        raise ValueError(
            "El orden de las variables del manifiesto es incompatible con el "
            "preprocesado actual."
        )

    model_path = bundle_path / MODEL_FILENAME
    if not model_path.exists():
        raise ValueError(f"No se encuentra el estimador en {bundle_path}")

    estimator = joblib.load(model_path)

    return LoadedModelBundle(estimator=estimator, manifest=manifest)


def infer_wine_quality(
    bundle: LoadedModelBundle,
    request: WineQualityRequest,
) -> WineQualityPrediction:
    """Preprocesa, invoca el estimador y valida la respuesta."""
    features = preprocess_wine_request(request).as_vector()

    prediction_label = bundle.estimator.predict([features])[0]

    # Invariante de salida: bloquear etiquetas fuera de contrato
    if prediction_label not in bundle.manifest.output_labels:
        raise ValueError(
            f"Etiqueta de inferencia desconocida o no permitida: {prediction_label}"
        )

    probabilities = bundle.estimator.predict_proba([features])[0]
    confidence = max(probabilities)

    return WineQualityPrediction(
        quality_band=prediction_label,  # type: ignore
        confidence=confidence,
        model_version=bundle.manifest.model_version,
        preprocessing_version=bundle.manifest.preprocessing_version,
    )