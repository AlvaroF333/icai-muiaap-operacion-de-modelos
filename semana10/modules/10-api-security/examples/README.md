# Demos de la clase 1

Cuatro aplicaciones FastAPI de un solo archivo, una por bloque de teoría, y un
`locustfile.py` para la prueba de carga de la demo final. Siguen las
convenciones de la skill oficial de FastAPI instalada en
`.claude/skills/fastapi`: `Annotated` con alias de dependencias (`ClientDep`,
`ClaimsDep`, `SettingsDep`), dependencias comunes en el `APIRouter`, tipos de
retorno y funciones `def` cuando el código no es asíncrono.

Desde `semana10/modules/10-api-security`:

```bash
uv sync --locked
uv run fastapi dev examples/api_key_demo.py
```

| Archivo | Bloque | Qué enseña |
| --- | --- | --- |
| [`api_key_demo.py`](api_key_demo.py) | 1 y 2 · Autenticación y autorización | `APIKeyHeader(auto_error=False)`, `secrets.compare_digest`, `401` con `WWW-Authenticate`, `require_scope` como factoría de dependencias y `403` declarado en el `APIRouter`. |
| [`jwt_demo.py`](jwt_demo.py) | 2 · JWT | `HTTPBearer`, `jwt.decode` con lista blanca de algoritmos, `aud`, `iss` y `exp`; un `POST /token` que simula al IdP solo para la demo. |
| [`cors_demo.py`](cors_demo.py) | 3 · CORS | `CORSMiddleware` con orígenes, métodos y cabeceras explícitos; preflight permitido y rechazado; `expose_headers`. |
| [`limits_demo.py`](limits_demo.py) | 4 · Secretos y límites | `BaseSettings` con prefijo `DEMO_`, `SecretStr`, fallo al arrancar sin clave, ventana fija con reloj inyectable y `429` con `Retry-After`. |
| [`locustfile.py`](locustfile.py) | 4 · Carga | `HttpUser`, `wait_time`, tareas con peso y clave leída de `LOCUST_API_KEY`. |
| [`../tests/test_examples.py`](../tests/test_examples.py) | Todos | `401`/`403`/`200`, JWT válido, caducado, con otra audiencia y con otra firma, preflight CORS, `429` con reloj falso y configuración desde el entorno con `monkeypatch`. |

Las claves que aparecen en `api_key_demo.py` (`demo-front-key` y
`demo-ops-key`) y el secreto por defecto de `jwt_demo.py` son **de demo y
públicos a propósito**. En el workshop las claves salen de la configuración y
nunca del código.

## Comandos de la demo en vivo

Cada demo escucha en `http://127.0.0.1:8000`; detén el servidor con `Ctrl+C`
antes de arrancar la siguiente.

```bash
# 1-2 · API key y scopes
uv run fastapi dev examples/api_key_demo.py

# 3 · JWT
uv run fastapi dev examples/jwt_demo.py

# 4 · CORS
uv run fastapi dev examples/cors_demo.py

# 5 · Configuración y rate limit (sin DEMO_API_KEY no arranca)
DEMO_API_KEY=demo-limits-key uv run fastapi dev examples/limits_demo.py

# 6 · Carga: API con límite 60/min en una terminal y Locust en otra
DEMO_API_KEY=demo-limits-key DEMO_RATE_LIMIT_PER_MINUTE=60 \
  uv run fastapi dev examples/limits_demo.py
LOCUST_API_KEY=demo-limits-key uv run --group load locust \
  -f examples/locustfile.py --headless -u 20 -r 5 -t 1m \
  --host http://127.0.0.1:8000
```

Los `curl` de cada paso están en el docstring de cada archivo y en la
[guía de la clase 1](../guides/class-1-theory-demo.md). En PowerShell, las
variables se fijan con `$env:DEMO_API_KEY="demo-limits-key"` antes del comando.

Locust está en el grupo de dependencias `load` para no instalarlo en cada
`uv sync`. Prepáralo antes de clase con `uv sync --locked --group load`.

## Comprobación de las demos

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

Resultado esperado: `19 passed` y Ruff sin errores. `locustfile.py` no tiene
tests: se comprueba ejecutándolo contra una demo arrancada.
