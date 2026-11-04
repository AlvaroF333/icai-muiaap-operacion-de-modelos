"""Reempaqueta el bundle de mi entrega S4 al formato del contrato oficial de S4.

Mi `save_model_bundle` de S4 guardó el estimador directamente en `model.joblib`,
mientras que el `load_model_bundle` oficial (el que usa el gateway de S5) espera
un mapa `{"estimator": ...}`. Este script NO reentrena ni modifica nada: carga el
mismo estimador y el mismo manifiesto y los vuelve a escribir con
`save_model_bundle` oficial en un directorio nuevo.

Uso (desde la raíz del repositorio; reutiliza el entorno del starter 5.2, que ya
tiene joblib, scikit-learn y pydantic):

    uv run --project semana5/modules/05-streamlit-basic-model-ui/exercises/\
02-first-streamlit/problem/starter python semana5/entrega/repack_s4_bundle.py \
        --input  semana4/solucionSemana4/models/wine_quality_bundle \
        --output semana5/models/wine_quality_bundle
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import joblib

REPO_ROOT = Path(__file__).resolve().parents[2]
S4_SOURCE = (
    REPO_ROOT
    / "semana4/modules/04-model-packaging/solutions"
    / "01.02-serializable-inference-module/src"
)


def repack(input_path: Path, output_path: Path) -> None:
    """Copia estimador y manifiesto de S4 al formato `{"estimator": ...}`."""

    sys.path.insert(0, str(S4_SOURCE))
    from model_packaging.artifact import ArtifactManifest, save_model_bundle

    if output_path.resolve() == input_path.resolve():
        raise ValueError("La salida debe ser distinta de la entrada.")

    payload = joblib.load(input_path / "model.joblib")
    estimator = payload["estimator"] if isinstance(payload, dict) else payload
    manifest = ArtifactManifest.model_validate(
        json.loads((input_path / "manifest.json").read_text(encoding="utf-8"))
    )
    save_model_bundle(output_path, estimator, manifest)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    repack(arguments.input, arguments.output)
    print(f"Bundle reempaquetado en: {arguments.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
