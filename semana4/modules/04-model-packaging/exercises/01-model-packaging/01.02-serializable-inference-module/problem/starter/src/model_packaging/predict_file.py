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
    predictions_buffer: list[dict[str, str | float]] = []

    with input_path.open("r", encoding="utf-8") as f_in:
        reader = csv.DictReader(f_in)
        for row in reader:
            if "sample_id" not in row or not row["sample_id"].strip():
                raise ValueError("sample_id es obligatorio y no puede estar vacío.")

            # sample_id se excluye del contrato del modelo y se guarda aparte
            sample_id = row.pop("sample_id").strip()

            # Falla con ValueError si alguna fila viola el contrato de entrada
            request = WineQualityRequest.model_validate(row)

            prediction = infer_wine_quality(bundle, request)

            output_row: dict[str, str | float] = {"sample_id": sample_id}
            output_row.update(prediction.model_dump())
            predictions_buffer.append(output_row)

    # Escritura atómica: si cualquier fila previa falló, el archivo nunca se crea
    if predictions_buffer:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="", encoding="utf-8") as f_out:
            writer = csv.DictWriter(
                f_out, fieldnames=list(predictions_buffer[0].keys())
            )
            writer.writeheader()
            writer.writerows(predictions_buffer)

    return len(predictions_buffer)


def parse_args() -> argparse.Namespace:
    """Declara la interfaz del comando público."""
    parser = argparse.ArgumentParser(
        description="Inferencia batch sobre un CSV usando un bundle empaquetado."
    )
    parser.add_argument(
        "--input", required=True, type=Path, help="Ruta al CSV de entrada"
    )
    parser.add_argument(
        "--output", required=True, type=Path, help="Ruta al CSV de salida"
    )
    parser.add_argument(
        "--bundle",
        default=DEFAULT_BUNDLE_PATH,
        type=Path,
        help="Ruta al bundle del modelo",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    count = predict_file(
        input_path=arguments.input,
        output_path=arguments.output,
        bundle_path=arguments.bundle,
    )
    print(f"Inferencia completada con éxito. Registros procesados: {count}")
