# Starter — Wine Quality API (punto de partida de S10)

Es la API `1.1.0` de S9: salida tipada, errores con un único sobre, OpenAPI
completo y una suite de tests. Le falta la seguridad: hoy cualquiera puede
predecir sin identificarse y sin límite. La configuración ya se lee con
`pydantic-settings` (`WINE_API_MODE` está migrada como ejemplo) y el limitador
ya se crea en `create_app`, pero ni autentica ni cuenta nada.

## Preparación

Desde este directorio:

```bash
uv sync --locked --group load
uv run pytest -q
```

Resultado esperado al empezar: `44 failed, 34 passed`. Los 34 en verde son la
regresión de S9 (`test_health.py` y `test_s9_*.py`); cada test en rojo de
`test_s10_*.py` corresponde a un TODO. Los tests no leen tu `.env` ni tus
variables `WINE_API_*`: cada uno construye su configuración.

## Arrancar la API

`pyproject.toml` declara el entrypoint en `[tool.fastapi]`:

```bash
uv run fastapi dev
```

Abre <http://127.0.0.1:8000/docs>. Cuando termines S10.1, crea tu configuración
local y cambia las claves de ejemplo por otras aleatorias:

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

A partir de S10.2, prueba con la clave de `front` de tu `.env`:

```bash
curl -i -X POST http://127.0.0.1:8000/v1/predictions \
  -H "X-API-Key: <clave-front>" -H "Content-Type: application/json" \
  -d '{"features": {"fixed_acidity": 7.4, "volatile_acidity": 0.7, "citric_acid": 0.0, "residual_sugar": 1.9, "chlorides": 0.076, "free_sulfur_dioxide": 11.0, "total_sulfur_dioxide": 34.0, "density": 0.9978, "ph": 3.51, "sulphates": 0.56, "alcohol": 9.4}}'
```

En PowerShell, las variables se fijan con `$env:WINE_API_MODE="unavailable"`
antes de `uv run fastapi dev`.

## Mapa del código

| Archivo | Estado | TODO |
| --- | --- | --- |
| `src/wine_api/settings.py` | `Settings` con `mode` y `SettingsConfigDict` | S10.1a–b |
| `.env.example` | Solo `WINE_API_MODE` | S10.1c |
| `src/wine_api/schemas.py` | Contratos de S9, `ClientUsage` y `UsageResponse` | S10.2a |
| `src/wine_api/errors.py` | Jerarquía y manejadores de S9 | S10.2b–c, S10.3a, S10.4a |
| `src/wine_api/security.py` | `AuthenticatedClient` y `ClientDep` declarados | S10.2d–e, S10.3b |
| `src/wine_api/rate_limit.py` | `RateLimitDecision`, `usage()` y `RateLimiterDep` | S10.4b–c |
| `src/wine_api/routers/predictions.py` | Ruta de S9 sin protección | S10.2f, S10.3c, S10.4d, S10.6a |
| `src/wine_api/routers/admin.py` | Router vacío | S10.3d, S10.6a |
| `src/wine_api/main.py` | `create_app(predictor, settings, rate_limiter)` | S10.5a–b, S10.6b |
| `contracts/openapi.json` | Contrato `1.1.0` de S9 | S10.6c (regenerar) |
| `locustfile.py` | Usuario con tareas de predicción y salud | S10.7a–b |
| `reports/README.md` | Plantilla del informe de carga | S10.7c |
| `src/wine_api/dependencies.py` | `PredictorDep`, `RequestIdDep`, `SettingsDep` (no se toca) | — |
| `src/wine_api/predictor.py`, `request_id.py`, `export_openapi.py` | No se tocan | — |
| `tests/` | Regresión de S9 y aceptación de S10 (no se tocan) | — |

Busca todos los TODO con:

```bash
grep -rn "TODO S10" src .env.example locustfile.py reports
```

## Comprobaciones por paso

```bash
uv run pytest -q tests/test_s10_1_settings.py        # 8 tests
uv run pytest -q tests/test_s10_2_authentication.py  # 8 tests
uv run pytest -q tests/test_s10_3_authorization.py   # 5 tests
uv run pytest -q tests/test_s10_4_rate_limit.py      # 7 tests
uv run pytest -q tests/test_s10_5_cors.py            # 7 tests
uv run pytest -q tests/test_s10_6_openapi.py         # 9 tests
uv run pytest -q tests/test_health.py tests/test_s9_*.py  # regresión: 34 tests
uv run ruff check .
uv run ruff format --check .
```

Checkpoints de la suite completa: 42 en verde tras S10.1, 52 tras S10.2, 58
tras S10.3, 65 tras S10.4, 72 tras S10.5 y 78 tras S10.6.

Para S10.7, con la API arrancada en otra terminal:

```bash
LOCUST_API_KEY=<clave-front> uv run --group load locust -f locustfile.py \
  --headless -u 20 -r 5 -t 1m --host http://127.0.0.1:8000 --csv reports/s10
```

## Pistas de investigación

- `BaseSettings`, `SettingsConfigDict(env_prefix=..., env_file=...)` y tipos
  complejos en variables de entorno: documentación de pydantic-settings,
  «Settings Management» y «Parsing environment variable values».
- `SecretStr`: documentación de Pydantic, «Secret Types».
- `APIKeyHeader`, `Security` y `auto_error`: documentación de FastAPI,
  «Security» y la referencia de `fastapi.security`.
- `secrets.compare_digest`: documentación de la biblioteca estándar de Python,
  módulo `secrets`.
- Dependencias en el router y «factorías» de dependencias: FastAPI,
  «Dependencies in path operation decorators» y «Advanced Dependencies».
- Cabeceras desde una dependencia: FastAPI, «Response - Change Headers».
- `Retry-After` y `429`: RFC 9110 §10.2.3 y RFC 6585 §4.
- `CORSMiddleware`: FastAPI, «CORS (Cross-Origin Resource Sharing)».
- Locust: «Writing a locustfile», `catch_response` y «Retrieve test statistics
  in CSV format».
