# Clase 1 — Teoría: serialización, errores, OpenAPI y tests (2 h)

## Objetivo

Entender qué le falta a una API que ya responde para que otra persona pueda
consumirla, mantenerla y probarla: un contrato de salida, errores predecibles,
una documentación que no miente y tests que lo demuestren.

## Secuencia

| Tiempo | Bloque | Diapositivas | Demo | Microejercicio |
| ---: | --- | --- | --- | --- |
| 10 min | Introducción | 1–5 | — | — |
| 30 min | 1 · Serialización | 6–12 | `examples/serialization_demo.py` | M1 |
| 30 min | 2 · Errores | 13–18 | `examples/errors_demo.py` | M2 |
| 25 min | 3 · OpenAPI | 19–23 | `examples/openapi_demo.py` | M3 |
| 20 min | 4 · Tests | 24–28 | `tests/test_examples.py` | M4 |
| 5 min | Resumen y preparación del workshop | 29 | — | — |

Los microejercicios están en
[`exercises/01-api-microexercises`](../../exercises/01-api-microexercises/problem/README.md).

## Preparación del docente

Desde `semana9/modules/09-api-professional`:

```bash
uv sync --locked
uv run pytest -q
```

Debe mostrar `9 passed`. Ten abiertos `/docs` y `/openapi.json` de cada demo en
pestañas separadas.

## Resultado esperado

Al terminar, el alumnado sabe explicar con sus palabras:

- por qué un tipo de retorno filtra campos internos y qué cambia con
  `response_model`;
- qué status y qué `error.code` corresponden a cada fallo, y qué nunca debe salir
  en un error;
- dónde vive cada parte del contrato OpenAPI y cómo se declara;
- cómo probar un `503` sin romper un modelo real.

## Antes de la clase 2

Pide que cada persona ejecute en el starter del workshop:

```bash
cd exercises/02-wine-api-hardening/problem/starter
uv sync --locked
uv run pytest -q
```

Resultado esperado: `23 failed, 4 passed`.
