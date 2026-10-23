# Semana 9 — API profesional: serialización, errores, OpenAPI y tests

La semana convierte la API funcional de S8 en una interfaz que otra persona
puede consumir, mantener y probar sin preguntar nada. El contrato público de S7
no cambia: se hace cumplir, se documenta y se prueba.

## Dos clases de 2 horas

- **Clase 1 — teoría (2 h):** serialización avanzada con Pydantic v2, errores
  predecibles con un único sobre, OpenAPI con docstrings y ejemplos, y tests con
  `TestClient`, `dependency_overrides` y snapshot del contrato. Cada bloque
  tiene una demo ejecutable y un microejercicio de 5 minutos.
- **Clase 2 — workshop (2 h):** la Wine Quality API pasa de `1.0.0` a `1.1.0`
  completando cuatro pasos guiados por una suite de aceptación.

## Acceso al material

- [Diapositivas](slides/README.md)
- [Módulo 09-api-professional](modules/09-api-professional/README.md)
- [Enunciado del workshop](modules/09-api-professional/exercises/02-wine-api-hardening/README.md)

**Requisitos:** Python 3.12 o superior y `uv`. Cada subproyecto (demos, starter y
solución) tiene su propio `uv.lock` y se prepara con `uv sync --locked`.

## Entregable

API documentada y testeada en versión `1.1.0`: `uv run pytest -q` sin fallos,
`contracts/openapi.json` versionado, Ruff en verde, captura de `/docs` y una nota
breve sobre compatibilidad del contrato.
