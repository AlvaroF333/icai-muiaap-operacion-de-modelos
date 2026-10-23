# Ejercicio 01 — Práctica: Wine Quality API protegida (2.0.0)

## Reto

Parte de la API de S9 (`1.1.0`), documentada y testeada pero abierta a
cualquiera, y añádele la seguridad mínima de producción:

- cada cliente se identifica con una API key en la cabecera `X-API-Key`;
- cada clave tiene scopes: `front` solo predice y `ops` además consulta el
  consumo en `GET /v1/admin/usage`;
- cada cliente tiene una cuota por minuto; al superarla recibe `429` con
  `Retry-After`;
- solo el front de Streamlit puede leer la API desde un navegador (CORS);
- claves, orígenes y opciones se leen de la configuración (`.env`), nunca del
  código;
- una prueba de carga con Locust deja evidencia de latencia, RPS y porcentaje de
  `429`.

`GET /health` sigue siendo público y el contrato de S7–S9 (payloads, sobre de
error y `request_id`) no cambia. Exigir autenticación sí rompe a los clientes
anónimos: la API pasa a `2.0.0`.

Duración: **2 horas** (clase 2 de la semana).

## Trabajo del alumnado

Parte del [starter](problem/starter/README.md) y completa los TODO en este
orden:

| Paso | Min | TODO | Qué decides | Comprobación |
| --- | ---: | --- | --- | --- |
| S10.1 · Configuración y secretos | 15 | `settings.py`, `.env.example` | Qué se configura, con qué tipos y qué valores por defecto son seguros (sin clientes, todo cerrado). | `tests/test_s10_1_settings.py` (8) |
| S10.2 · Autenticación | 25 | `schemas.py`, `errors.py`, `security.py`, `routers/predictions.py` | Cómo se lee y compara la clave, qué responde la API cuando falta o es incorrecta y qué se registra en el log. | `tests/test_s10_2_authentication.py` (8) |
| S10.3 · Autorización | 15 | `errors.py`, `security.py`, `routers/predictions.py`, `routers/admin.py` | Qué scope exige cada router y qué expone `GET /v1/admin/usage` sin filtrar claves. | `tests/test_s10_3_authorization.py` (5) |
| S10.4 · Rate limiting | 25 | `errors.py`, `rate_limit.py`, `routers/predictions.py` | Cómo se cuenta la ventana fija, cuánto vale `Retry-After` y en qué orden van autenticación y límite. | `tests/test_s10_4_rate_limit.py` (7) |
| S10.5 · CORS y documentación | 10 | `main.py` | Qué orígenes, métodos y cabeceras se permiten y cuándo se ocultan `/docs`, `/redoc` y `/openapi.json`. | `tests/test_s10_5_cors.py` (7) |
| S10.6 · Contrato 2.0.0 | 10 | `main.py`, `routers/*.py`, `contracts/openapi.json` | Qué versión semántica toca y cómo se documentan 401, 403 y 429. | `tests/test_s10_6_openapi.py` (9) |
| S10.7 · Prueba de carga | 10 | `locustfile.py`, `reports/README.md` | Qué carga se simula y qué dicen p50, p95, RPS y `% 429`. | Evidencia en `reports/`, no `pytest` |

Al empezar, `uv run pytest -q` da **34 tests en verde y 44 en rojo**. Los 34 en
verde son la regresión de S9 y no deben ponerse en rojo en ningún momento. Los
checkpoints esperados son 42 en verde tras S10.1, 52 tras S10.2, 58 tras S10.3,
65 tras S10.4, 72 tras S10.5 y los 78 tras S10.6 (77 hasta que regeneras
`contracts/openapi.json`).

## Restricciones de diseño

- No modifiques `predictor.py`, `request_id.py`, `export_openapi.py` ni ningún
  test. Si un test te parece incorrecto, coméntalo con el docente.
- Autenticación, scopes y rate limit se declaran como dependencias en
  `dependencies=[...]` del `APIRouter`, no ruta a ruta ni en `include_router()`.
- Las dependencias lanzan errores de dominio (`AuthenticationError`,
  `PermissionDeniedError`, `RateLimitExceededError`); nunca `HTTPException`. El
  manejador de S9 produce el sobre común.
- Ninguna respuesta, log ni `repr` puede contener una API key, ni la válida ni
  la que ha enviado un atacante.
- Compara claves con `secrets.compare_digest`, nunca con `==`.
- CORS con orígenes explícitos desde la configuración: nunca `"*"` ni
  `allow_credentials=True`.
- Ninguna clave real en el repositorio: `.env.example` solo lleva valores
  `cambia-...` y `.env` está en `.gitignore`.
- `GET /health` sigue siendo público y no consume cuota.
- Sigue las convenciones de la skill de FastAPI del repositorio: `Annotated`
  con alias de dependencias, tipos de retorno, parámetros comunes en el
  `APIRouter`, sin `...` como valor por defecto y funciones `def` para código no
  asíncrono.
- No hagas llamadas de red reales desde los tests: el reloj del rate limit se
  inyecta.

## Entrega

- Código con la API en versión `2.0.0` y `uv run pytest -q` sin fallos.
- `contracts/openapi.json` regenerado con
  `uv run python -m wine_api.export_openapi` y versionado en Git.
- `uv run ruff check .` y `uv run ruff format --check .` en verde.
- `.env.example` completo con valores de ejemplo; `git check-ignore .env`
  confirma que `.env` no se versiona.
- `reports/README.md` completo y los CSV de Locust (`reports/s10_*.csv`).
- Captura de `/docs` con el botón **Authorize**, `POST /v1/predictions`
  desplegado y sus respuestas `401`, `403` y `429`.
- Nota breve (5–10 líneas): por qué la API pasa a `2.0.0`, qué tiene que cambiar
  el front de S7 para seguir funcionando y dónde guardaría su clave.

## Rúbrica

| Criterio | Peso | Evidencia |
| --- | ---: | --- |
| Configuración y secretos fuera del código | 15 % | S10.1 en verde; `.env.example` con placeholders y `.env` ignorado. |
| Autenticación correcta y segura | 20 % | S10.2 en verde; `compare_digest`; la clave no aparece en respuestas ni logs. |
| Autorización por scopes | 15 % | S10.3 en verde; dependencias en el `APIRouter`; `usage` sin claves. |
| Rate limiting por cliente | 20 % | S10.4 en verde; `Retry-After` entero; reloj inyectable. |
| CORS y documentación configurables | 10 % | S10.5 en verde; sin `"*"`. |
| Contrato 2.0.0 documentado | 10 % | S10.6 en verde, captura de `/docs` y nota de versionado. |
| Evidencia de carga | 10 % | `reports/` con CSV y análisis de p50, p95, RPS y `% 429`. |

La [solución de referencia](../../solutions/01-wine-api-security/README.md) se
consulta después de la entrega.
