"""Punto de extensión del CLI de inferencia sobre un bundle."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from model_packaging.artifact import (
    DEFAULT_BUNDLE_PATH,
    infer_wine_quality,
    load_model_bundle,
)
from model_packaging.contracts import WineQualityRequest


def predict_file(
    input_path: Path,
    output_path: Path,
    bundle_path: Path,
) -> int:
    """Valida todas las filas y escribe el CSV solo al final."""
    bundle = load_model_bundle(bundle_path)
    predictions_buffer = []

    with input_path.open("r", encoding="utf-8") as f_in:
        reader = csv.DictReader(f_in)
        for row in reader:
            # sample_id se excluye del contrato del modelo y se guarda aparte
            sample_id = row.pop("sample_id")

            # Falla con ValueError si alguna fila viola el contrato de entrada
            request = WineQualityRequest.model_validate(row)

            prediction = infer_wine_quality(bundle, request)

            output_row = {"sample_id": sample_id}
            output_row.update(prediction.model_dump())
            predictions_buffer.append(output_row)

    # Escritura atómica: si cualquier fila previa falló, el archivo nunca se crea
    if predictions_buffer:
        with output_path.open("w", newline="", encoding="utf-8") as f_out:
            writer = csv.DictWriter(
                f_out, fieldnames=list(predictions_buffer[0].keys())
            )
            writer.writeheader()
            writer.writerows(predictions_buffer)

    return len(predictions_buffer)


def parse_args() -> argparse.Namespace:
    """Declara la interfaz del comando público."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--bundle", default=DEFAULT_BUNDLE_PATH, type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    raise SystemExit(
        predict_file(
            input_path=arguments.input,
            output_path=arguments.output,
            bundle_path=arguments.bundle,
        )
    )