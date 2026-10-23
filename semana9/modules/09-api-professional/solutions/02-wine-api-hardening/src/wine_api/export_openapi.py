"""Exporta el contrato OpenAPI versionado en `contracts/openapi.json`."""

import json
import sys
from pathlib import Path

from wine_api.main import create_app

DEFAULT_PATH = Path("contracts/openapi.json")


def render_openapi() -> str:
    """Serializa el esquema de forma estable para poder compararlo en Git."""

    schema = create_app().openapi()
    return json.dumps(schema, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def main() -> None:
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_openapi(), encoding="utf-8")
    print(f"OpenAPI escrito en {target}")


if __name__ == "__main__":
    main()
