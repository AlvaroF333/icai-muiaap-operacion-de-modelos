# Ejercicio 02 — Workshop: Wine Quality API v1.1

## Reto

Parte de la API de S8, que ya funciona, y conviértela en una interfaz que otra
persona pueda consumir, mantener y probar sin preguntarte nada. El contrato
público de S7 (`POST /v1/predictions`, `GET /health` y el sobre de error con
`code`, `message`, `fields` y `request_id`) no cambia: en S9 se hace cumplir y
se documenta.

Duración: **2 horas** (clase 2 de la semana).

## Trabajo del alumnado

Parte del [starter](problem/starter/README.md) y completa los TODO en este
orden:

| Paso | TODO | Qué decides | Comprobación |
| --- | --- | --- | --- |
| S9.1 · Salida | `schemas.py`, `routers/*.py` | Qué campos son públicos, cómo se redondea `confidence` y cómo se escribe `served_at`. | `tests/test_s9_1_output_contract.py` |
| S9.2 · Errores | `errors.py`, `routers/health.py` | Qué status y qué `error.code` recibe cada fallo, sin filtrar detalles internos. | `tests/test_s9_2_errors.py` |
| S9.3 · OpenAPI | `main.py`, `schemas.py`, `routers/*.py` | Qué lee quien consume la API en `/docs`: metadatos, tags, docstrings, errores y ejemplos. | `tests/test_s9_3_openapi.py` |
| S9.4 · Tests propios | `tests/test_s9_4_student.py` | Qué casos demuestran el contrato: `503` con overrides, rangos y snapshot de OpenAPI. | Tus propios tests en verde |

Al empezar, `uv run pytest -q` da **4 tests en verde y 23 en rojo**. Los
checkpoints esperados son 8 en verde tras S9.1, 16 tras S9.2, 23 tras S9.3 y la
suite completa tras S9.4.

## Restricciones de diseño

- No modifiques `predictor.py`, `request_id.py`, `dependencies.py` ni los tests
  de S9.1–S9.3. Si un test te parece incorrecto, coméntalo con el docente.
- No uses `HTTPException` en el dominio: las rutas lanzan errores de dominio y
  los manejadores deciden el status.
- Ningún error puede devolver trazas, rutas de ficheros, el texto de una
  excepción ni el `input` recibido.
- Sigue las convenciones de la skill de FastAPI del repositorio: tipos de
  retorno, `Annotated`, parámetros comunes en el `APIRouter`, sin `...` como
  valor por defecto y funciones `def` para código bloqueante.
- No hagas llamadas de red reales desde los tests.

## Entrega

- Código con la API en versión `1.1.0` y `uv run pytest -q` sin fallos.
- `contracts/openapi.json` generado con `uv run python -m wine_api.export_openapi`
  y versionado en Git.
- `uv run ruff check .` y `uv run ruff format --check .` en verde.
- Captura de `/docs` con la operación de predicción desplegada, sus errores
  `400`, `422` y `503` y los ejemplos de cuerpo.
- Nota breve (5–10 líneas): qué cambio de esta semana es compatible, qué cambio
  rompería a los clientes de S7 y cómo lo versionarías.

## Rúbrica

| Criterio | Peso | Evidencia |
| --- | ---: | --- |
| Contrato de salida tipado y filtrado | 25 % | S9.1 en verde; `raw_score` no aparece en ninguna respuesta. |
| Errores consistentes y seguros | 30 % | S9.2 en verde; ningún error devuelve `{"detail": ...}`. |
| OpenAPI útil para un consumidor | 20 % | S9.3 en verde y captura de `/docs`. |
| Tests propios con intención | 20 % | S9.4: override, casos límite parametrizados y snapshot. |
| Calidad y explicación | 5 % | Ruff en verde y nota de compatibilidad. |

La [solución de referencia](../../solutions/02-wine-api-hardening/README.md) se
consulta después de la entrega.
