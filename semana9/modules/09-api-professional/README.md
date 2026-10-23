# Módulo 09 — API profesional: serialización, errores, OpenAPI y tests

La API de S8 ya responde. Este módulo la convierte en una interfaz mantenible:
la salida se valida y se filtra, todos los errores comparten un sobre estable,
OpenAPI documenta lo que la API hace de verdad y una suite de tests lo
demuestra en cada cambio.

## Dos clases de 2 horas

| Clase | Formato | Guion | Material |
| --- | --- | --- | --- |
| 1 | Teoría con demos y microejercicios | [sessions/01-teoria-api-profesional](sessions/01-teoria-api-profesional/README.md) | [examples/](examples/README.md), [exercises/01-api-microexercises](exercises/01-api-microexercises/problem/README.md) |
| 2 | Workshop guiado por tests | [sessions/02-workshop-wine-api](sessions/02-workshop-wine-api/README.md) | [exercises/02-wine-api-hardening](exercises/02-wine-api-hardening/README.md) |

Guías docentes con timing, pistas y errores frecuentes:
[clase 1](guides/class-1-theory.md) · [clase 2](guides/class-2-workshop.md).

Diapositivas: [semana9/slides](../../slides/README.md).

## Estructura

```text
09-api-professional/
├── pyproject.toml, uv.lock        # entorno de las demos
├── examples/                      # una demo FastAPI por bloque de teoría
├── tests/test_examples.py         # tests de las demos (bloque 4)
├── sessions/                      # guion de cada clase
├── guides/                        # timing, pistas y criterios de revisión
├── exercises/
│   ├── 01-api-microexercises/     # microejercicios de la clase 1
│   └── 02-wine-api-hardening/     # workshop: enunciado y starter
└── solutions/
    └── 02-wine-api-hardening/     # referencia docente del workshop
```

## Comprobaciones

```bash
uv sync --locked
uv run pytest -q
uv run ruff check .
```

Starter y solución son subproyectos independientes con su propio `uv.lock`:

```bash
cd exercises/02-wine-api-hardening/problem/starter && uv sync --locked && uv run pytest -q
cd solutions/02-wine-api-hardening && uv sync --locked && uv run pytest -q
```

Resultados esperados: demos `9 passed`; starter `23 failed, 4 passed`;
solución `35 passed`.

## Convenciones de FastAPI

El código sigue la skill oficial de FastAPI instalada en
`.claude/skills/fastapi` del repositorio: tipos de retorno antes que
`response_model`, `Annotated` con alias de dependencias (`PredictorDep`),
`prefix`, `tags` y `responses` en el `APIRouter`, sin `...` como valor por
defecto, funciones `def` para código bloqueante, `fastapi dev` con
`[tool.fastapi]` en `pyproject.toml`, y uv, Ruff (reglas `FAST`) y HTTPX como
herramientas.

## Continuidad

- **S7** definió el contrato y el sobre de error; **S8** lo implementó con
  FastAPI.
- **S9** lo hace cumplir y lo documenta sin romper a los clientes de S7.
- **S10** protegerá estos endpoints; los tests de hoy son su red de seguridad.
