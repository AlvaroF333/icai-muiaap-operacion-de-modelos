# Guía docente — Clase 2: workshop (2 h)

## Antes de empezar

- En `solutions/02-wine-api-hardening`: `uv sync --locked` y `uv run pytest -q`
  → `35 passed`.
- En el starter: `uv run pytest -q` → `23 failed, 4 passed`.
- Proyecta las diapositivas 30–33 y deja visible la 32 (plan) durante la sesión.

## Timing y checkpoints

| Minuto | Paso | Checkpoint (tests en verde) |
| ---: | --- | ---: |
| 0–25 | Arranque (`grep -rn "TODO S9" src tests`) y S9.1 · Contrato de salida | 8 |
| 25–55 | S9.2 · Errores | 16 |
| 55–80 | S9.3 · OpenAPI | 23 |
| 80–110 | S9.4 · Tests propios | Todos |
| 110–120 | Debrief y revisión cruzada de `/docs` | — |

En cada checkpoint, pregunta en voz alta cuántos tests tiene cada persona en
verde y desbloquea a quien vaya dos pasos por detrás.

## Pistas graduadas

Da la pista 1 primero; la 2 solo si sigue bloqueado tras 5 minutos.

### S9.1 · Contrato de salida

1. «Lo que no declares en `Prediction` no saldrá en la respuesta.»
2. «`Prediction.model_validate(output, from_attributes=True)` lee los atributos
   de la dataclass; mira la diapositiva 11.»

Error frecuente: redondear en el predictor. El test pasa, pero la decisión queda
en el lugar equivocado; pide que la muevan al `field_serializer`.

### S9.2 · Errores

1. «Imprime `exc.errors()` en un test con un payload inválido y mira `type` y
   `loc`.»
2. «El JSON roto llega como `RequestValidationError` con `type == "json_invalid"`.»

Errores frecuentes:

- Registrar `fastapi.HTTPException`: los `404` y `405` no pasan por el
  manejador.
- Copiar `exc` o `str(exc)` en el mensaje del `500`: falla
  `test_unexpected_error_hides_internal_details`.
- Olvidar S9.2f: `/health` sigue devolviendo `{"detail": ...}` en el `503`.

### S9.3 · OpenAPI

1. «`responses=` en el `APIRouter` se aplica a todas sus operaciones.»
2. «Si declaras el `422` con `ErrorResponse`, FastAPI deja de añadir
   `HTTPValidationError`.»

Error frecuente: poner `tags` en `include_router()`. Funciona, pero contradice la
convención de la skill y del enunciado; pide que lo muevan al router.

### S9.4 · Tests propios

1. «`client.app.dependency_overrides[get_predictor] = UnavailablePredictor`.»
2. «Para el snapshot, compara `json.loads(render_openapi())` con el archivo,
   no los textos: el orden de las claves ya es estable, pero el JSON es más
   robusto.»

## Revisión cruzada (debrief)

Por parejas, cada persona abre el `/docs` de la otra y comprueba la checklist de
la diapositiva 23: resumen, descripción y tag por operación; todos los status
con esquema; unidad, rango y ejemplo por campo. Cierra con la pregunta de la
nota de entrega: ¿qué cambio sería incompatible y cómo lo versionarías?

## Corrección rápida

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
grep -rn "raw_score" contracts/openapi.json || echo "ok: raw_score no es público"
grep -rn "pytest.fail" tests/test_s9_4_student.py || echo "ok: S9.4 completo"
```
