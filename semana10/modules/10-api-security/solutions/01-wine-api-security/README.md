# Solución de referencia — Wine Quality API 2.0.0 protegida

Referencia docente de la práctica de S10. Se consulta después de la entrega o
con autorización del docente.

## Preparación y comprobación

Desde este directorio:

```bash
uv sync --locked --group load
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
```

Resultado esperado: `78 passed` y Ruff sin errores. La suite es la misma que la
del starter: 34 tests de regresión de S9 y 44 de aceptación de S10.1–S10.6.

## Arrancar la API

```bash
cp .env.example .env      # y cambia las claves `cambia-...` por otras aleatorias
uv run fastapi dev
```

Sin `.env` la API arranca, pero sin clientes: todo endpoint protegido responde
`401` (fail closed). `WINE_API_MODE=unavailable uv run fastapi dev` sigue
simulando un modelo no cargado. `WINE_API_DOCS_ENABLED=false` oculta `/docs`,
`/redoc` y `/openapi.json`.

## Prueba de carga (S10.7)

Con la API arrancada en otra terminal:

```bash
LOCUST_API_KEY=<clave-front> uv run --group load locust -f locustfile.py \
  --headless -u 20 -r 5 -t 1m --host http://127.0.0.1:8000 --csv reports/s10
```

`reports/README.md` es la plantilla del informe. La solución no incluye
resultados: dependen de la máquina y de la configuración, y no deben copiarse.

## Decisiones de diseño

| Tema | Decisión | Dónde |
| --- | --- | --- |
| Configuración | `Settings(BaseSettings)` con prefijo `WINE_API_`, `.env` opcional y tipos validados al arrancar; `WINE_API_MODE` deja de leerse con `os.environ`. | `settings.py` |
| Secretos | `SecretStr` para cada clave: `repr`, `str` y `model_dump_json` muestran `**********`. `.env.example` solo lleva `cambia-...`. | `settings.py`, `.env.example` |
| Fail closed | Sin clientes configurados no hay clave válida: `401` en todo endpoint protegido, nunca acceso libre. | `settings.py`, `security.py` |
| Autenticación | `APIKeyHeader(auto_error=False)` para responder con el sobre propio; `compare_digest` sobre bytes (con `str` falla si llegan caracteres no ASCII); mismo `401` y mismo mensaje si falta o es incorrecta, con `WWW-Authenticate: ApiKey`. | `security.py`, `errors.py` |
| Autorización | `require_scope(scope)` es una factoría de dependencias; cada `APIRouter` declara la suya. Falta de scope es `403`, no `401`: la identidad es correcta. | `security.py`, `routers/` |
| Rate limiting | Ventana fija por cliente con reloj inyectable y `threading.Lock` (las dependencias `def` corren en un threadpool). `429` con `Retry-After` entero redondeado hacia arriba; `X-RateLimit-Limit` y `X-RateLimit-Remaining` en las respuestas permitidas. | `rate_limit.py` |
| Orden de dependencias | Autenticar → scope → cuota: un anónimo o un cliente sin permiso no consume cuota ajena. `GET /health` no pasa por ninguna. | `routers/predictions.py` |
| Cabeceras de error | `WineApiError` admite `headers` por instancia; `error_response` las copia sin perder `X-Request-Id`. | `errors.py` |
| Consumo | `GET /v1/admin/usage` (scope `admin`) devuelve nombre, peticiones en la ventana y límite; nunca la clave. | `routers/admin.py`, `schemas.py` |
| CORS | Orígenes desde `cors_origins` (se rechaza `"*"`), solo `GET`/`POST`, `Content-Type` y `X-API-Key`, sin credenciales; expone `X-Request-Id`, `Retry-After` y `X-RateLimit-Remaining`. Es el middleware más externo: el preflight no exige clave. | `main.py` |
| Documentación | `docs_enabled=False` quita `/docs`, `/redoc` y `/openapi.json`. Reduce lo que se anuncia, no protege nada por sí solo. | `main.py` |
| Logs | Se registra el intento rechazado con `request_id` y si había clave, nunca su valor. | `security.py`, `rate_limit.py` |
| OpenAPI | `APIKeyHeader` en `components.securitySchemes`; `401`, `403` y `429` (con `Retry-After`) documentados con `ErrorResponse` en el `APIRouter`. | `routers/`, `security.py`, `rate_limit.py` |
| Versionado | `1.1.0` → `2.0.0`: exigir `X-API-Key` rompe a los clientes anónimos de 1.x. La ruta sigue en `/v1` porque los payloads no cambian y el front de S7 se actualiza de forma coordinada para enviar la clave. | `main.py`, `contracts/openapi.json` |
| Tests | El `conftest` envía una clave de test, aísla el entorno (`WINE_API_*`) y no lee `.env`; el snapshot de OpenAPI se mueve de S9.4 a S10.6. | `tests/conftest.py`, `tests/support.py` |

## Regenerar el contrato

Si cambias la API a propósito:

```bash
uv run python -m wine_api.export_openapi
git diff contracts/openapi.json
```

## Puntos para el debrief

- El contador vive en la memoria del proceso: con `fastapi run --workers 2`
  cada worker cuenta por su lado y el límite efectivo se duplica. En producción,
  Redis o el API gateway.
- La ventana fija permite ráfagas de hasta el doble del límite en la frontera
  entre dos ventanas; ventana deslizante y token bucket lo suavizan.
- La búsqueda de la clave termina en el primer cliente que coincide; con pocos
  clientes es irrelevante, pero en un sistema real se guarda un hash de cada
  clave y se busca por él.
- CORS no autentica: `curl` y Locust ignoran CORS. La clave sigue siendo lo que
  protege la API; CORS solo decide qué páginas pueden leer la respuesta.
- Una API key en el JavaScript de un navegador es pública. El front de S7 es
  Streamlit y llama desde el servidor, por eso puede guardar la clave en su
  propia configuración.
