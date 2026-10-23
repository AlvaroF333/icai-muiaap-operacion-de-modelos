# Clase 2 — Práctica: Wine Quality API protegida (2 h)

## Objetivo

Aplicar la clase 1 a la API del proyecto: configuración y secretos con
`pydantic-settings`, API key con scopes, rate limiting por cliente, CORS desde la
configuración, contrato `2.0.0` y una prueba de carga con Locust, guiados por
una suite de aceptación.

## Secuencia

| Tiempo | Paso | Diapositivas | Tests en verde al cerrar |
| ---: | --- | --- | ---: |
| 15 min | Lectura del starter y S10.1 · Configuración y secretos | 31–34 | 42 |
| 25 min | S10.2 · Autenticación con API key | 33 | 52 |
| 15 min | S10.3 · Autorización por scopes y `/v1/admin/usage` | 33 | 58 |
| 25 min | S10.4 · Rate limiting por cliente | 33 | 65 |
| 10 min | S10.5 · CORS y `docs_enabled` | 33 | 72 |
| 20 min | S10.6 · Contrato 2.0.0 y S10.7 · Prueba de carga | 35 | 78 + informe |
| 10 min | Debrief y revisión de criterios | 36–37 | — |

Los 34 tests de regresión de S9 están en verde desde el principio y deben
seguir así en cada checkpoint.

## Material

- Enunciado: [`exercises/01-wine-api-security`](../../exercises/01-wine-api-security/README.md).
- Punto de partida: [`problem/starter`](../../exercises/01-wine-api-security/problem/starter/README.md).
- Referencia docente: [`solutions/01-wine-api-security`](../../solutions/01-wine-api-security/README.md).
- Guía con timing y pistas: [`guides/class-2-practice.md`](../../guides/class-2-practice.md).

## Resultado esperado

Cada persona termina con la API en versión `2.0.0`, `uv run pytest -q` sin
fallos, `contracts/openapi.json` regenerado, `.env.example` sin claves reales y
un informe de carga en `reports/`. Quien termine antes puede actualizar el
cliente HTTP del front de S7 para que envíe `X-API-Key` leída de su propia
configuración y muestre un mensaje comprensible ante `401`, `403` y `429`.
