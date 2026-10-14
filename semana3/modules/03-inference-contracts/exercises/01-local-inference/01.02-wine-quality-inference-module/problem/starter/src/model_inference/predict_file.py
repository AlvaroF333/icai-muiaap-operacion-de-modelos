"""Script local que aplica preprocesado e inferencia a un fichero CSV."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from pydantic import ValidationError

from model_inference.contracts import WineQualityPrediction, WineQualityRequest
from model_inference.inference import (
    DEFAULT_MODEL_PATH,
    infer_wine_quality,
    load_wine_quality_model,
)
from model_inference.preprocess import PREPROCESSING_VERSION, preprocess_wine_request

OUTPUT_FIELDS = (
    "sample_id",
    "quality_band",
    "confidence",
    "model_version",
    "preprocessing_version",
)


def predict_file(input_path: Path, output_path: Path, model_path: Path) -> int:
    """Genera un CSV de predicciones usando el mismo módulo para cada fila.

    Lee todas las filas del CSV, valida cada una contra el contrato,
    preprocesa y ejecuta la inferencia. Si alguna fila es inválida,
    lanza una excepción sin escribir el fichero de salida (atomicidad).
    """

    model = load_wine_quality_model(model_path)
    predictions: list[dict[str, str | float]] = []

    with input_path.open(newline="", encoding="utf-8") as source:
        rows = csv.DictReader(source)
        if not rows.fieldnames or "sample_id" not in rows.fieldnames:
            raise ValueError("El CSV de entrada debe incluir una columna sample_id.")

        for row_number, row in enumerate(rows, start=2):
            sample_id = row.pop("sample_id")
            if not sample_id or not sample_id.strip():
                raise ValueError(f"Fila {row_number} tiene un sample_id vacío.")
            try:
                request = WineQualityRequest.model_validate(row)
            except ValidationError as error:
                raise ValueError(
                    f"Fila {row_number} inválida para sample_id={sample_id}: {error}"
                ) from error

            features = preprocess_wine_request(request)
            quality_band, confidence = infer_wine_quality(model, features)
            prediction = WineQualityPrediction(
                quality_band=quality_band,
                confidence=confidence,
                model_version=model.model_version,
                preprocessing_version=PREPROCESSING_VERSION,
            )
            predictions.append({"sample_id": sample_id, **prediction.model_dump()})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as target:
        writer = csv.DictWriter(target, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(predictions)

    return len(predictions)


def parse_args() -> argparse.Namespace:
    """Declara la interfaz de línea de comandos del script local de inferencia."""

    parser = argparse.ArgumentParser(description="Inferencia local de calidad de vino")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", default=DEFAULT_MODEL_PATH, type=Path)
    return parser.parse_args()


def main() -> int:
    """Ejecuta la cadena contrato, preprocesado, inferencia y salida CSV."""

    parser = argparse.ArgumentParser(add_help=False)
    arguments = parse_args()
    try:
        prediction_count = predict_file(
            input_path=arguments.input,
            output_path=arguments.output,
            model_path=arguments.model,
        )
    except (FileNotFoundError, ValueError) as error:
        parser.error(str(error))

    print(f"Predicciones escritas: {prediction_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
