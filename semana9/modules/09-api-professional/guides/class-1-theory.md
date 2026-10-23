# Guía docente — Clase 1: teoría (2 h)

## Antes de empezar

- `uv sync --locked` y `uv run pytest -q` en la raíz del módulo: `9 passed`.
- Deck: [semana9/slides](../../../slides/README.md). Las notas del ponente de
  cada diapositiva llevan el guion y los tiempos.
- Ten preparada una terminal en `semana9/modules/09-api-professional`.

## Introducción (10 min, diapositivas 1–5)

Pregunta de apertura: «Mi API ya responde. ¿Puede otra persona consumirla,
mantenerla y probarla sin preguntarme nada?». Recoge respuestas y llévalas a los
tres huecos de S8: salida sin contrato, errores con formas distintas y nada que
avise si el contrato cambia.

## Bloque 1 · Serialización (30 min, diapositivas 6–12)

1. Demo: `uv run fastapi dev examples/serialization_demo.py`.
2. Abre `/v1/scores/leaky`: el `dict` expone `raw_score` y una ruta interna.
3. Abre `/v1/scores/public` y `/v1/scores/filtered`: mismo resultado público,
   dos mecanismos (tipo de retorno y `response_model`).
4. Enseña en `/docs` el esquema `PublicScore`, con `is_reliable` incluido.
5. Microejercicio M1 (5 min).

Pregunta de control: «¿Añadir un valor nuevo a `QualityBand` es compatible?».
Respuesta esperada: depende del cliente; si hace un `switch` exhaustivo, rompe.

## Bloque 2 · Errores (30 min, diapositivas 13–18)

1. Demo: `uv run fastapi dev examples/errors_demo.py`.
2. Comenta el decorador de `handle_validation` y enseña el `{"detail": ...}`
   por defecto, con el `input` del usuario dentro. Restáuralo.
3. `GET /v1/boom`: el secreto se queda en el log y el cliente recibe
   `internal_error`.
4. Microejercicio M2 (5 min).

Error frecuente: registrar `fastapi.HTTPException` en lugar de
`starlette.exceptions.HTTPException`; los `404` del router no pasan por el
manejador.

## Bloque 3 · OpenAPI (25 min, diapositivas 19–23)

1. Demo: `uv run fastapi dev examples/openapi_demo.py`.
2. Pon `/docs` y `/openapi.json` lado a lado y localiza `summary`, el docstring,
   `responses` y los ejemplos.
3. Ejecuta el ejemplo `minor` con «Try it out».
4. Microejercicio M3 (5 min).

Insiste en la convención de la skill de FastAPI: `prefix`, `tags` y `responses`
en el `APIRouter`, no en `include_router()`.

## Bloque 4 · Tests (20 min, diapositivas 24–28)

1. `uv run pytest -q` y recorrido por `tests/test_examples.py`.
2. Quita `raise_server_exceptions=False` del fixture y enseña cómo cambia el
   fallo; restáuralo.
3. Explica el snapshot de OpenAPI con el script `export_openapi` del workshop.
4. Microejercicio M4 (5 min).

## Cierre (5 min, diapositiva 29)

Pide que preparen el starter del workshop antes de la clase 2 (`uv sync
--locked` y `uv run pytest -q` con `23 failed, 4 passed`).

## Si falta tiempo

Recorta M3 y M4 a demostración del docente. No recortes el bloque 2: es el
requisito previo de la mitad del workshop.
