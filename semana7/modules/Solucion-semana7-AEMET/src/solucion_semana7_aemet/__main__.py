"""Ejecución de la práctica completa.

    uv run python -m solucion_semana7_aemet

1. Lee la API key de ``.env`` (variable ``API_AEMET``).
2. Llama al inventario de estaciones y obtiene el idema de
   "MADRID, CIUDAD UNIVERSITARIA".
3. Llama a la climatología diaria de octubre de 2019 para esa estación.
4. Guarda el JSON crudo y un CSV limpio en ``data/`` y muestra un resumen.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from solucion_semana7_aemet.client import AemetClient, AemetError
from solucion_semana7_aemet.transform import to_dataframe

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ESTACION = "MADRID, CIUDAD UNIVERSITARIA"
# Fechas tal y como las fija el enunciado (fin = 30 de octubre).
FECHA_INI = "2019-10-01T00:00:00UTC"
FECHA_FIN = "2019-10-30T23:59:59UTC"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--estacion", default=ESTACION)
    p.add_argument("--fecha-ini", default=FECHA_INI)
    p.add_argument("--fecha-fin", default=FECHA_FIN)
    p.add_argument("--out-dir", type=Path, default=PROJECT_ROOT / "data")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    load_dotenv(PROJECT_ROOT / ".env")
    api_key = os.getenv("API_AEMET", "")

    try:
        client = AemetClient(api_key)
        print(f"[1/2] Inventario de estaciones -> buscando {args.estacion!r}")
        idema = client.buscar_idema(args.estacion)
        print(f"      idema = {idema}")

        print(f"[2/2] Climatología diaria {args.fecha_ini} .. {args.fecha_fin}")
        registros = client.climatologia_diaria(args.fecha_ini, args.fecha_fin, idema)
    except (ValueError, AemetError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"climatologia_diaria_{idema}_{args.fecha_ini[:10]}_{args.fecha_fin[:10]}"
    raw_path = args.out_dir / f"{stem}.json"
    csv_path = args.out_dir / f"{stem}.csv"
    raw_path.write_text(
        json.dumps(registros, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    df = to_dataframe(registros)
    df.to_csv(csv_path, index=False)

    print(f"\n{len(df)} días descargados. Guardado en:\n  {raw_path}\n  {csv_path}\n")
    cols = [c for c in ["fecha", "tmin", "tmed", "tmax", "prec"] if c in df.columns]
    print(df[cols].to_string(index=False))
    if {"tmed", "tmax", "tmin", "prec"} <= set(df.columns):
        print(
            f"\nResumen: tmed media={df['tmed'].mean():.1f} ºC | "
            f"tmax={df['tmax'].max():.1f} ºC | tmin={df['tmin'].min():.1f} ºC | "
            f"prec total={df['prec'].sum():.1f} mm"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
