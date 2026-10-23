# Demos de la clase 1

Tres aplicaciones FastAPI de un solo archivo, una por bloque de teoría, y una
suite de tests que sirve a la vez de demo del bloque 4. Todas siguen las
convenciones de la skill oficial de FastAPI instalada en
`.claude/skills/fastapi`: tipos de retorno, `Annotated`, parámetros comunes en
el `APIRouter` y funciones `def` cuando el código no es asíncrono.

Desde `semana9/modules/09-api-professional`:

```bash
uv sync --locked
uv run fastapi dev examples/serialization_demo.py
```

| Archivo | Bloque | Qué enseña |
| --- | --- | --- |
| [`serialization_demo.py`](serialization_demo.py) | 1 · Serialización | Fuga de campos internos con un `dict`, tipo de retorno, `response_model`, `field_serializer`, `computed_field` y `response_model_exclude_none`. |
| [`errors_demo.py`](errors_demo.py) | 2 · Errores | Error de dominio, `exception_handler`, reescritura del `422`, `404` de Starlette y `500` sin secretos. |
| [`openapi_demo.py`](openapi_demo.py) | 3 · OpenAPI | Metadatos, `openapi_tags`, `summary`, docstring, `responses`, `json_schema_extra` y `openapi_examples`. |
| [`../tests/test_examples.py`](../tests/test_examples.py) | 4 · Tests | `TestClient`, `raise_server_exceptions=False`, `parametrize`, `dependency_overrides` y comprobaciones sobre `/openapi.json`. |

Cambia de demo deteniendo el servidor con `Ctrl+C` y arrancando el siguiente
archivo. Las tres escuchan en `http://127.0.0.1:8000` y exponen `/docs`,
`/redoc` y `/openapi.json`.

Comprobación de las demos:

```bash
uv run pytest -q
uv run ruff check .
```

Los datos y modelos son deterministas y docentes: ningún score representa una
decisión real de crédito ni de calidad.
