# Semana 10 — API protegida: autenticación, autorización, CORS y límites

La API de S9 ya es profesional, pero está abierta: cualquiera que conozca la URL
puede usarla sin límite. Esta semana se añade la seguridad mínima de producción:
API keys con scopes, secretos y configuración fuera del código, rate limiting
por cliente, CORS restringido y una prueba de carga con Locust que lo demuestra.

## Dos clases de 2 horas

- **Clase 1 — teoría y demo (1 h 30 + 30 min):** autenticación frente a
  autorización, API keys y JWT, CORS y preflight, secretos con
  `pydantic-settings`, rate limiting con `429` y `Retry-After`, e introducción a
  Locust. Cierra con una demo en vivo de 30 minutos sobre las demos del módulo.
- **Clase 2 — práctica (2 h):** la Wine Quality API pasa de `1.1.0` a `2.0.0`
  completando siete pasos guiados por una suite de aceptación y una prueba de
  carga.

## Acceso al material

- [Diapositivas](slides/README.md)
- [Módulo 10-api-security](modules/10-api-security/README.md)
- [Enunciado de la práctica](modules/10-api-security/exercises/01-wine-api-security/README.md)

**Requisitos:** Python 3.12 o superior y `uv`. Cada subproyecto (demos, starter y
solución) tiene su propio `uv.lock` y se prepara con `uv sync --locked`. Locust
está en el grupo `load`: `uv sync --locked --group load`.

## Entregable

API protegida en versión `2.0.0`: `uv run pytest -q` sin fallos, validación por
API key con scopes, rate limiting con `429` y `Retry-After`, CORS desde la
configuración, secretos fuera del código (`.env.example` con valores de
ejemplo y `.env` sin versionar), `contracts/openapi.json` regenerado e informe
de carga con Locust en `reports/`.
