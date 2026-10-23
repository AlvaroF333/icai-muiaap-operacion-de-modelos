# Clase 2 — Workshop: Wine Quality API v1.1 (2 h)

## Objetivo

Aplicar los cuatro bloques de la clase 1 a la API del proyecto: salida tipada,
errores consistentes, OpenAPI rico y tests propios, guiados por una suite de
aceptación.

## Secuencia

| Tiempo | Paso | Diapositivas | Tests en verde al cerrar |
| ---: | --- | --- | ---: |
| 25 min | Lectura del starter y S9.1 · Contrato de salida | 30–33 | 8 |
| 30 min | S9.2 · Errores | 32 | 16 |
| 25 min | S9.3 · OpenAPI | 32 | 23 |
| 30 min | S9.4 · Tests propios | 32 | Todos |
| 10 min | Debrief y revisión cruzada de `/docs` | 34–35 | — |

## Material

- Enunciado: [`exercises/02-wine-api-hardening`](../../exercises/02-wine-api-hardening/README.md).
- Punto de partida: [`problem/starter`](../../exercises/02-wine-api-hardening/problem/starter/README.md).
- Referencia docente: [`solutions/02-wine-api-hardening`](../../solutions/02-wine-api-hardening/README.md).
- Guía con timing y pistas: [`guides/class-2-workshop.md`](../../guides/class-2-workshop.md).

## Resultado esperado

Cada persona termina con la API en versión `1.1.0`, `uv run pytest -q` sin
fallos, `contracts/openapi.json` versionado y una captura de `/docs`. Quien
termine antes puede conectar su propio bundle de S4 detrás del protocolo
`Predictor` sin tocar los routers.
