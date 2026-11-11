"""Conversión de la respuesta de climatologías diarias a un DataFrame tipado.

AEMET devuelve TODOS los valores como texto y con coma decimal ("15,2"), y usa
marcas especiales como "Ip" (precipitación inapreciable, < 0,1 mm) o "Varias"
en las horas. Aquí se normaliza para poder analizar los datos.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

NUMERIC_COLUMNS = [
    "altitud",
    "tmed",
    "prec",
    "tmin",
    "tmax",
    "dir",
    "velmedia",
    "racha",
    "sol",
    "presMax",
    "presMin",
    "hrMedia",
    "hrMax",
    "hrMin",
]


def _to_number(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    if text.lower() == "ip":  # precipitación inapreciable
        return 0.0
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return None


def to_dataframe(registros: list[dict[str, Any]]) -> pd.DataFrame:
    df = pd.DataFrame(registros)
    if df.empty:
        return df
    df["fecha"] = pd.to_datetime(df["fecha"], format="%Y-%m-%d")
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = df[col].map(_to_number).astype("float64")
    return df.sort_values("fecha").reset_index(drop=True)
