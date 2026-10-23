# Starter — Wine Quality API (punto de partida de S9)

Es la API de S8: funciona, valida la entrada con Pydantic y carga el predictor
una sola vez en el `lifespan`. Le faltan tres cosas que vas a añadir hoy: un
contrato de salida, errores consistentes y documentación OpenAPI fiel, más los
tests que lo demuestren.

## Preparación

Desde este directorio:

```bash
uv sync --locked
uv run pytest -q
```

Resultado esperado al empezar: `23 failed, 4 passed`. Cada test en rojo
corresponde a un TODO.

## Arrancar la API

`pyproject.toml` declara el entrypoint en `[tool.fastapi]`, así que no hace
falta indicar el archivo:

```bash
uv run fastapi dev
```

Abre <http://127.0.0.1:8000/docs>. Para simular un modelo no cargado:

```bash
WINE_API_MODE=unavailable uv run fastapi dev
```

En PowerShell: `$env:WINE_API_MODE="unavailable"; uv run fastapi dev`.

## Mapa del código

| Archivo | Estado | TODO |
| --- | --- | --- |
| `src/wine_api/main.py` | `create_app`, `lifespan`, middleware y routers | S9.3g metadatos |
| `src/wine_api/schemas.py` | Entrada y sobre de error completos | S9.1a–c, S9.3d |
| `src/wine_api/errors.py` | Excepciones y `error_response` | S9.2a–e |
| `src/wine_api/routers/health.py` | Ruta funcional con `dict` | S9.1d, S9.2f, S9.3a–b |
| `src/wine_api/routers/predictions.py` | Ruta funcional con `dict` | S9.1e, S9.3a, S9.3c, S9.3e–f |
| `src/wine_api/predictor.py` | Predictor determinista (no se toca) | — |
| `src/wine_api/request_id.py` | `X-Request-Id` por petición (no se toca) | — |
| `src/wine_api/dependencies.py` | `PredictorDep` y `RequestIdDep` (no se toca) | — |
| `src/wine_api/export_openapi.py` | Exporta `contracts/openapi.json` | Se usa en S9.4d |
| `tests/test_s9_4_student.py` | Cuatro tests en `pytest.fail` | S9.4a–d |

Busca todos los TODO con:

```bash
grep -rn "TODO S9" src tests
```

## Comprobaciones por paso

```bash
uv run pytest -q tests/test_s9_1_output_contract.py
uv run pytest -q tests/test_s9_2_errors.py
uv run pytest -q tests/test_s9_3_openapi.py
uv run pytest -q tests/test_s9_4_student.py
uv run ruff check .
uv run ruff format --check .
```

## Pistas de investigación

- Tipos de retorno frente a `response_model`: documentación de FastAPI,
  «Response Model - Return Type».
- `field_serializer` y `from_attributes`: documentación de Pydantic v2,
  «Serialization» y «Models».
- `RequestValidationError.errors()`: cada elemento trae `type`, `loc`, `msg` e
  `input`. Imprime uno con un test antes de escribir el manejador.
- `responses=` y `openapi_examples=`: FastAPI, «Additional Responses in
  OpenAPI» y «Declare Request Example Data».
- `app.dependency_overrides`: FastAPI, «Testing Dependencies with Overrides».
