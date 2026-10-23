# Guía docente — Clase 2: práctica (2 h)

## Antes de empezar

- En `solutions/01-wine-api-security`: `uv sync --locked --group load` y
  `uv run pytest -q` → `78 passed`.
- En el starter: `uv run pytest -q` → `44 failed, 34 passed`.
- Proyecta las diapositivas 31–34 y deja visible la 33 (plan) durante la sesión.
- Recuerda que los 34 tests en verde del starter son la regresión de S9: si
  alguno se pone en rojo, la persona ha roto algo que ya funcionaba.

## Timing y checkpoints

| Minuto | Paso | Checkpoint (tests en verde) |
| ---: | --- | ---: |
| 0–15 | Arranque (`grep -rn "TODO S10" src .env.example locustfile.py reports`) y S10.1 · Configuración | 42 |
| 15–40 | S10.2 · Autenticación | 52 |
| 40–55 | S10.3 · Autorización y `/v1/admin/usage` | 58 |
| 55–80 | S10.4 · Rate limiting | 65 |
| 80–90 | S10.5 · CORS y `docs_enabled` | 72 |
| 90–100 | S10.6 · Contrato 2.0.0 | 78 (77 hasta regenerar el contrato) |
| 100–110 | S10.7 · Locust e informe (diapositiva 35) | Informe |
| 110–120 | Debrief y criterios (diapositivas 36–37) | — |

En cada checkpoint, pregunta en voz alta cuántos tests tiene cada persona en
verde y desbloquea a quien vaya dos pasos por detrás. Si alguien no llega a
S10.7 en clase, la prueba de carga se puede hacer en casa: solo necesita la API
arrancada.

## Pistas graduadas

Da la pista 1 primero; la 2 solo si sigue bloqueado tras 5 minutos.

### S10.1 · Configuración y secretos

1. «`clients` es un `dict[str, ClientConfig]`: pydantic-settings lo lee de una
   variable en JSON.»
2. «En `.env`, envuelve el JSON en comillas simples para que las comillas
   dobles lleguen intactas; `Settings(_env_file=".env.example")` te sirve para
   comprobarlo en una consola.»

Errores frecuentes:

- Poner una clave real en `.env.example` o subir `.env`: falla
  `test_env_example_documents_every_setting_with_placeholders` o la revisión.
- Default `cors_origins=["*"]` «para que funcione»: el validador debe
  rechazarlo.
- `key: str` en lugar de `SecretStr`: la clave sale en `repr(settings)`.

### S10.2 · Autenticación

1. «La dependencia recibe la clave con `Annotated[str | None,
   Security(api_key_header)]`; con `auto_error=False` llega `None` si falta.»
2. «Recorre `settings.clients.items()` y compara bytes con
   `secrets.compare_digest`; si nada coincide, `raise AuthenticationError()`.»

Errores frecuentes:

- `auto_error=True`: el `401` llega como `{"detail": ...}` y falla el sobre.
- Comparar `str` con `compare_digest`: el caso `non-ascii` da `500`.
- Olvidar S10.2b: el `401` sale sin `WWW-Authenticate` porque `error_response`
  ignora las cabeceras del error.
- Proteger cada ruta por separado en lugar del `APIRouter`.
- Escribir la clave recibida en el log: falla
  `test_api_keys_never_appear_in_responses_or_logs`.

### S10.3 · Autorización

1. «`require_scope` devuelve una función; esa función es la dependencia.»
2. «En el router: `dependencies=[Depends(require_scope("admin"))]`; la ruta
   recibe `SettingsDep` y `RateLimiterDep` para construir `UsageResponse`.»

Errores frecuentes:

- Devolver `401` por falta de scope: la identidad es correcta, es `403`.
- Construir `usage` a partir de `ClientConfig` con `model_dump()`: la clave
  sale enmascarada, pero sale. Falla `test_usage_never_exposes_keys`.
- Olvidar `summary` o docstring en la ruta nueva: falla
  `test_every_operation_has_summary_docstring_and_tag` de la regresión de S9.

### S10.4 · Rate limiting

1. «Cuatro casos en `hit`: sin ventana, ventana caducada, cuota llena y cuota
   con hueco. Dibuja la línea de tiempo antes de programar.»
2. «`retry_after` es lo que falta para `start + window_seconds`, redondeado con
   `math.ceil`; las cabeceras de éxito se ponen en el `response: Response` que
   recibe la dependencia.»

Errores frecuentes:

- Usar `time.time()` o `time.monotonic()` dentro de `hit`: el reloj falso de los
  tests no tiene efecto.
- Contar también la petición denegada: la ventana nunca se libera del todo.
- Poner `enforce_rate_limit` antes que el scope o declararla en `main.py`: un
  anónimo o un cliente sin permiso gasta cuota.
- `Retry-After` como `float` o con `int()`: sale `"44.5"` o un segundo de menos.

### S10.5 · CORS y documentación

1. «`add_middleware(CORSMiddleware, ...)` después de `app.middleware("http")`:
   el último añadido es el más externo y responde al preflight.»
2. «`docs_url`, `redoc_url` y `openapi_url` aceptan `None`.»

Error frecuente: escribir el origen como `http://127.0.0.1:8501` cuando el
front se abre en `http://localhost:8501`. Para el navegador son orígenes
distintos.

### S10.6 · Contrato 2.0.0

1. «`responses=` en el `APIRouter` se aplica a todas sus operaciones; un 429
   admite `headers` en OpenAPI.»
2. «Después de cambiar `API_VERSION`, regenera con
   `uv run python -m wine_api.export_openapi` y revisa el `git diff`.»

Error frecuente: subir a `1.2.0`. Pregunta: «¿Funciona el front de S7 sin
cambios contra esta API?». Si la respuesta es no, es un cambio mayor.

### S10.7 · Prueba de carga

1. «`self.client.headers["X-API-Key"] = ...` en `on_start`, con la clave de
   `LOCUST_API_KEY`.»
2. «`with self.client.post(..., catch_response=True) as response:` y decide tú
   con `response.success()` o `response.failure(...)`.»

Errores frecuentes:

- Todo son `401`: falta `LOCUST_API_KEY` o no coincide con `.env`.
- Interpretar los `429` como un fallo del servicio: son la política de cuotas
  funcionando. Para medir capacidad hace falta un cliente con un límite alto.
- Copiar cifras de otra persona: los números dependen de la máquina.

## Debrief (10 min)

Recorre los criterios de la diapositiva 36 con una entrega voluntaria
proyectada: `/docs` con **Authorize**, `curl` sin clave (`401`), `front` en
`/v1/admin/usage` (`403`) y el `% 429` del informe. Cierra con las preguntas
de la nota de entrega: ¿por qué `2.0.0`?, ¿qué cambia en el front de S7? y ¿qué
pasaría con el contador en memoria al escalar a dos réplicas en S11–S12?

## Corrección rápida

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
grep -rn "TODO S10" src .env.example locustfile.py reports || echo "ok: sin TODO"
git check-ignore -q .env && echo "ok: .env ignorado"
git ls-files | grep -E '(^|/)\.env$' && echo "ERROR: .env versionado"
grep -n "compare_digest" src/wine_api/security.py
grep -rn '"\*"' src/wine_api/main.py || echo "ok: sin comodín en CORS"
uv run python -c "import json; print(json.load(open('contracts/openapi.json'))['info']['version'])"
ls reports/s10_stats.csv reports/s10_failures.csv
```
