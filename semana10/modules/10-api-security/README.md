# Módulo 10 — API protegida: autenticación, autorización, CORS y límites

La API de S9 está documentada y testeada, pero cualquiera que conozca la URL
puede usarla sin límite. Este módulo añade la seguridad mínima de producción:
cada cliente se identifica con una API key, solo hace lo que sus scopes
permiten, consume dentro de una cuota, los navegadores solo la leen desde
orígenes conocidos y ningún secreto vive en el código. Una prueba de carga con
Locust deja la evidencia.

## Dos clases de 2 horas

| Clase | Formato | Guion | Material |
| --- | --- | --- | --- |
| 1 | 1 h 30 de teoría + 30 min de demo en vivo | [sessions/01-teoria-seguridad](sessions/01-teoria-seguridad/README.md) | [examples/](examples/README.md) |
| 2 | Práctica guiada por tests (2 h) | [sessions/02-practica-api-protegida](sessions/02-practica-api-protegida/README.md) | [exercises/01-wine-api-security](exercises/01-wine-api-security/README.md) |

Guías docentes con timing, pistas y errores frecuentes:
[clase 1](guides/class-1-theory-demo.md) · [clase 2](guides/class-2-practice.md).

Diapositivas: [semana10/slides](../../slides/README.md).

## Estructura

```text
10-api-security/
├── pyproject.toml, uv.lock        # entorno de las demos (grupo `load` con Locust)
├── examples/                      # una demo por bloque + locustfile.py
├── tests/test_examples.py         # tests de las demos
├── sessions/                      # guion de cada clase
├── guides/                        # timing, pistas y criterios de revisión
├── exercises/
│   └── 01-wine-api-security/      # práctica: enunciado y starter
└── solutions/
    └── 01-wine-api-security/      # referencia docente de la práctica
```

## Comprobaciones

```bash
uv sync --locked
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

Starter y solución son subproyectos independientes con su propio `uv.lock`:

```bash
cd exercises/01-wine-api-security/problem/starter && uv sync --locked && uv run pytest -q
cd solutions/01-wine-api-security && uv sync --locked && uv run pytest -q
```

Resultados esperados: demos `19 passed`; starter `44 failed, 34 passed`;
solución `78 passed`. Los 34 tests en verde del starter son la regresión de S9:
deben seguir en verde durante toda la práctica.

La prueba de carga no forma parte de `pytest`: necesita la API arrancada y se
lanza con `uv run --group load locust ...` (ver
[examples/README.md](examples/README.md) y el
[enunciado](exercises/01-wine-api-security/README.md)).

## Convenciones de FastAPI

El código sigue la skill oficial de FastAPI instalada en
`.claude/skills/fastapi` del repositorio: `Annotated` con alias de dependencias
(`ClientDep`, `SettingsDep`, `RateLimiterDep`), autenticación, scopes y rate
limit declarados en `dependencies=[...]` del `APIRouter`, `responses` comunes en
el router, tipos de retorno, funciones `def` para código no asíncrono,
`fastapi dev` con `[tool.fastapi]` en `pyproject.toml`, y uv, Ruff (reglas
`FAST`) y HTTPX como herramientas.

## Continuidad

- **S7** fijó el contrato y **S8** lo implementó; **S9** lo hizo cumplir, lo
  documentó y lo cubrió con tests.
- **S10** lo protege. Exigir `X-API-Key` rompe a los clientes anónimos, por eso
  la API pasa a `2.0.0`; el front de S7 se actualiza a la vez para enviar la
  clave, que lee de su propia configuración.
- **S11** empaquetará la API en una imagen Docker: la configuración por
  variables de entorno de hoy es lo que permitirá ejecutarla sin reconstruirla.
