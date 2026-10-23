# Solución de referencia — Wine Quality API v1.1

Referencia docente del workshop de S9. Se consulta después de la entrega o con
autorización del docente.

## Preparación y comprobación

Desde este directorio:

```bash
uv sync --locked
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

Resultado esperado: `35 passed` y Ruff sin errores. La suite comparte con el
starter los tests de S9.1–S9.3; `tests/test_s9_4_student.py` es la versión de
referencia de los tests del alumnado.

## Arrancar la API

```bash
uv run fastapi dev
WINE_API_MODE=unavailable uv run fastapi dev
```

## Decisiones de diseño

| Tema | Decisión | Dónde |
| --- | --- | --- |
| Contrato de salida | Tipo de retorno `-> PredictionResponse`; `ModelOutput` es interno y `raw_score` nunca sale. | `routers/predictions.py`, `predictor.py` |
| Serialización | `confidence` con dos decimales y `served_at` en UTC con `Z`, decididos en el esquema público. | `schemas.py` |
| Entrada estricta | `extra="forbid"` y `strict=True`: los enteros valen; los booleanos y los textos no. | `schemas.py` |
| Errores | Jerarquía `WineApiError` con atributos de clase y cuatro manejadores: validación, dominio, Starlette y último recurso. | `errors.py` |
| 400 frente a 422 | `json_invalid` es `400 invalid_json`; un JSON válido fuera de contrato es `422 validation_error`. | `errors.py` |
| Trazabilidad | `request_id` en el cuerpo y en `X-Request-Id`, también en los `500`. | `request_id.py`, `errors.py` |
| OpenAPI | Metadatos y tags en `FastAPI(...)`; prefijo, tags y errores comunes en el `APIRouter`; docstrings para el consumidor; tres `openapi_examples`. | `main.py`, `routers/` |
| Versionado | `1.0.0` → `1.1.0`: `served_at` es un campo nuevo y compatible. | `main.py` |
| Snapshot | `contracts/openapi.json` versionado y comparado en un test. | `export_openapi.py`, `tests/test_s9_4_student.py` |

## Regenerar el contrato

Si cambias la API a propósito:

```bash
uv run python -m wine_api.export_openapi
git diff contracts/openapi.json
```

Revisa el diff, decide si el cambio es compatible y actualiza `API_VERSION` en
`main.py` antes de volver a exportar.

## Puntos para el debrief

- El manejador de `Exception` lo ejecuta `ServerErrorMiddleware`, por fuera del
  middleware de `request_id`; por eso `error_response` añade la cabecera
  `X-Request-Id` también en los `500`.
- Se registra `starlette.exceptions.HTTPException` y no la de FastAPI para
  capturar también los `404` y `405` que genera el router.
- Sin `with TestClient(app)` no se ejecuta el `lifespan` y `app.state.predictor`
  no existe.
