# Guía docente — Clase 1: teoría y demo (2 h)

## Antes de empezar

- `uv sync --locked --group load` y `uv run pytest -q` en la raíz del módulo:
  `19 passed`.
- Deck: [semana10/slides](../../../slides/README.md). Las notas del ponente de
  cada diapositiva llevan el guion y los tiempos.
- Dos terminales en `semana10/modules/10-api-security`: **T1** para la API y
  **T2** para `curl` y Locust. `jq` instalado para el paso 3 de la demo.
- Las claves de las demos (`demo-front-key`, `demo-ops-key`,
  `demo-limits-key`) son públicas a propósito. Dilo en voz alta la primera vez
  que aparezcan.

## Timing

| Minuto | Bloque | Diapositivas |
| ---: | --- | --- |
| 0–10 | Introducción | 1–5 |
| 10–35 | 1 · Autenticación | 6–11 |
| 35–60 | 2 · Autorización y JWT | 12–17 |
| 60–75 | 3 · CORS | 18–21 |
| 75–90 | 4 · Secretos, límites y carga | 22–27 |
| 90–120 | Demo en vivo y resumen | 28–30 |

## Introducción (10 min, diapositivas 1–5)

Pregunta de apertura: «La API de S9 está documentada y testeada. Si mañana
publico su URL, ¿qué puede pasar?». Recoge respuestas y llévalas a cinco
preguntas que estructuran la clase: ¿quién llama?, ¿qué puede hacer?, ¿desde
qué web?, ¿cuánto puede consumir? y ¿dónde viven los secretos?

## Bloque 1 · Autenticación (25 min, diapositivas 6–11)

- Autenticación responde «¿quién eres?» (`401`); autorización, «¿qué puedes
  hacer?» (`403`). Pon la diferencia en la pizarra y vuelve a ella en cada
  bloque.
- Mecanismos: API key, Bearer JWT, OAuth2/OIDC, mTLS. Para un servicio de
  inferencia consumido por otros servicios, una API key por cliente es el
  mínimo razonable.
- Fragmento A de `api_key_demo.py`: `APIKeyHeader(auto_error=False)`,
  `compare_digest` y `401` con `WWW-Authenticate`.

Preguntas de control:

- «¿Puedo mandar la clave en la URL, `?api_key=...`?». No: queda en logs de
  acceso, historial del navegador y cabecera `Referer`.
- «¿Por qué `compare_digest` y no `==`?». `==` se para en el primer carácter
  distinto y el tiempo de respuesta filtra cuántos caracteres acertaste.

## Bloque 2 · Autorización y JWT (25 min, diapositivas 12–17)

- Fragmento B: `require_scope` es una factoría de dependencias y cada
  `APIRouter` declara la suya en `dependencies=[...]`. Conecta con la
  convención de la skill de FastAPI: lo común va en el router.
- JWT: cabecera, payload y firma separados por puntos. El payload está
  codificado en base64url, **no cifrado**: cualquiera lo lee.
- Fragmento C de `jwt_demo.py`: `algorithms=["HS256"]` es una lista blanca;
  `audience` e `issuer` evitan aceptar tokens emitidos para otra API.

Pregunta de control: «¿Qué ventaja tiene un JWT frente a una API key?». La API
valida el token sin consultar una base de datos y el token caduca solo; a
cambio, revocarlo antes de `exp` exige una lista de revocación o tokens cortos.

## Bloque 3 · CORS (15 min, diapositivas 18–21)

- CORS lo aplica el navegador: decide qué páginas pueden **leer** la respuesta.
  No autentica a nadie y no frena a `curl` ni a Locust.
- Preflight `OPTIONS` con `Origin`, `Access-Control-Request-Method` y
  `Access-Control-Request-Headers`.
- Fragmento D de `cors_demo.py`: orígenes, métodos y cabeceras explícitos;
  `expose_headers` para que el JavaScript lea `X-Request-Id`.

Pregunta de control: «¿Si pongo `allow_origins=["*"]` está más segura o
menos?». Menos: cualquier web lee las respuestas, y combinado con credenciales
(cookies) una web ajena podría actuar con la sesión de quien la visita.

## Bloque 4 · Secretos, límites y carga (15 min, diapositivas 22–27)

- Fragmento E de `limits_demo.py`: `BaseSettings` con prefijo, `.env` opcional y
  `SecretStr`. La configuración se valida al arrancar: si falta la clave, la
  aplicación no arranca.
- Fragmento F: ventana fija con reloj inyectable. `429` con `Retry-After`
  entero, redondeado hacia arriba.
- Fragmento G de `locustfile.py`: usuarios, `wait_time`, tareas con peso y
  clave desde el entorno.
- Checklist de la diapositiva 27: es la misma que revisa la práctica.

## Demo en vivo (30 min, diapositivas 28–29)

Proyecta la diapositiva 29 con el guion y sigue estos pasos. Los resultados
indicados son los que devuelven las demos.

### Paso 1 · API key (5 min)

```bash
# T1
uv run fastapi dev examples/api_key_demo.py

# T2: sin clave
curl -i -X POST http://127.0.0.1:8000/v1/scores \
  -H "Content-Type: application/json" -d '{"age": 42, "income": 38000}'
# T2: con la clave de front
curl -i -X POST http://127.0.0.1:8000/v1/scores -H "X-API-Key: demo-front-key" \
  -H "Content-Type: application/json" -d '{"age": 42, "income": 38000}'
```

Se ve: `401` con `www-authenticate: ApiKey` y `{"detail":"Invalid API key"}`;
después `200` con `{"client":"front","score":0.38}`. Abre `/docs` y enseña el
botón **Authorize** que aparece por usar `Security(api_key_header)`.

### Paso 2 · Scopes (5 min)

```bash
curl -i http://127.0.0.1:8000/v1/admin/usage -H "X-API-Key: demo-front-key"
curl -i http://127.0.0.1:8000/v1/admin/usage -H "X-API-Key: demo-ops-key"
```

Se ve: `403` con `{"detail":"Missing scope: admin"}` y después `200` con el
contador por cliente, por ejemplo `{"requests":{"front":1}}`. Pregunta: «¿Por
qué `front` recibe 403 y no 401?».

### Paso 3 · JWT (5 min)

```bash
# T1 (Ctrl+C a la demo anterior)
uv run fastapi dev examples/jwt_demo.py

# T2: token válido
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/token \
  -H "Content-Type: application/json" -d '{"sub": "ana"}' | jq -r .access_token)
curl -i http://127.0.0.1:8000/v1/me -H "Authorization: Bearer $TOKEN"

# T2: el payload se lee sin conocer el secreto
uv run python -c "import jwt, sys; print(jwt.decode(sys.argv[1], options={'verify_signature': False}))" "$TOKEN"

# T2: caducado y con otra audiencia (solo la demo permite fabricarlos)
EXPIRED=$(curl -s -X POST http://127.0.0.1:8000/token -H "Content-Type: application/json" \
  -d '{"sub": "ana", "expires_in": -60}' | jq -r .access_token)
curl -i http://127.0.0.1:8000/v1/me -H "Authorization: Bearer $EXPIRED"
OTHER=$(curl -s -X POST http://127.0.0.1:8000/token -H "Content-Type: application/json" \
  -d '{"sub": "ana", "audience": "otra-api"}' | jq -r .access_token)
curl -i http://127.0.0.1:8000/v1/me -H "Authorization: Bearer $OTHER"
```

Se ve: `200` con `sub`, `scope` y `expires_at`; el payload completo en claro;
y `401` con `{"detail":"Invalid token"}` y `www-authenticate: Bearer` en los dos
últimos. Insiste: `POST /token` simula al proveedor de identidad; una API de
inferencia no emite sus propios tokens.

### Paso 4 · CORS (5 min)

```bash
# T1
uv run fastapi dev examples/cors_demo.py

# T2: preflight desde el front de Streamlit
curl -i -X OPTIONS http://127.0.0.1:8000/v1/scores \
  -H "Origin: http://localhost:8501" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: content-type,x-api-key"
# T2: preflight desde un origen desconocido
curl -i -X OPTIONS http://127.0.0.1:8000/v1/scores \
  -H "Origin: https://evil.example" -H "Access-Control-Request-Method: POST"
# T2: la misma petición real desde curl
curl -i -X POST http://127.0.0.1:8000/v1/scores -H "Origin: https://evil.example" \
  -H "Content-Type: application/json" -d '{"age": 42, "income": 38000}'
```

Se ve: `200` con `access-control-allow-origin: http://localhost:8501`; `400`
con `Disallowed CORS origin`; y en la última, `200` **sin**
`access-control-allow-origin`: `curl` lee la respuesta, un navegador no la
entregaría al JavaScript. Es la prueba de que CORS no sustituye a la clave.

### Paso 5 · Configuración y rate limit (5 min)

```bash
# T1: sin clave no arranca (ValidationError: api_key Field required)
uv run fastapi dev examples/limits_demo.py
# T1: con clave
DEMO_API_KEY=demo-limits-key uv run fastapi dev examples/limits_demo.py

# T2: siete peticiones con límite 5/min
for i in $(seq 1 7); do
  curl -s -o /dev/null -w "%{http_code} " -X POST http://127.0.0.1:8000/v1/scores \
    -H "X-API-Key: demo-limits-key" -H "Content-Type: application/json" \
    -d '{"age": 42, "income": 38000}'
done; echo
curl -i -X POST http://127.0.0.1:8000/v1/scores -H "X-API-Key: demo-limits-key" \
  -H "Content-Type: application/json" -d '{"age": 42, "income": 38000}'
curl -s http://127.0.0.1:8000/v1/config -H "X-API-Key: demo-limits-key"
```

Se ve: `200 200 200 200 200 429 429`; un `429` con `retry-after` en segundos
enteros; y la configuración con `"api_key":"**********"`. Si guardas un archivo
durante la demo, `fastapi dev` recarga y el contador vuelve a cero: úsalo para
explicar por qué el estado en memoria no sirve con varias réplicas.

### Paso 6 · Locust (5 min)

```bash
# T1: límite de 60/min
DEMO_API_KEY=demo-limits-key DEMO_RATE_LIMIT_PER_MINUTE=60 \
  uv run fastapi dev examples/limits_demo.py

# T2: 20 usuarios, 5 nuevos por segundo, 1 minuto
LOCUST_API_KEY=demo-limits-key uv run --group load locust \
  -f examples/locustfile.py --headless -u 20 -r 5 -t 1m \
  --host http://127.0.0.1:8000
```

Lee en la tabla final `# reqs`, `# fails` y `req/s`, y en la tabla de
percentiles las columnas `50%` y `95%`. Estimación, no medida: con 20 usuarios y una espera media de 1,25 s, Locust pide del
orden de 800 predicciones por minuto y el límite deja pasar 60: la mayoría de
`POST /v1/scores` son `429` (Locust los cuenta como fallos), mientras que
`GET /health` no falla. Si sobra tiempo, repite contra `api_key_demo.py` con
`LOCUST_API_KEY=demo-front-key`: sin límite, `0` fallos, y la latencia mide el
servicio, no la política de cuotas.

## Resumen (diapositiva 30)

Vuelve a las cinco preguntas de la introducción y asocia a cada una su
mecanismo: API key, scopes, CORS, rate limit y `pydantic-settings`. Pide que
preparen el starter de la práctica (`uv sync --locked --group load` y
`uv run pytest -q` con `44 failed, 34 passed`).

## Errores frecuentes

- `APIKeyHeader()` con `auto_error=True` (valor por defecto): FastAPI responde
  con su propio `{"detail": ...}` y en la práctica se rompe el sobre de S9.
- Comparar claves con `==` o guardarlas en el código o en Git.
- Aplicar el rate limit antes de autenticar: un anónimo agota la cuota de un
  cliente legítimo.
- `Retry-After` con decimales o redondeado hacia abajo (puede salir `0`).
- `jwt.decode` sin `algorithms=` o sin `audience`: acepta tokens que no son
  para esta API.
- Guardar datos sensibles en el payload de un JWT: se lee sin la clave.
- Pensar que CORS protege la API frente a `curl` o un script.
- `allow_origins=["*"]` «para que funcione»: el problema suele ser un origen mal
  escrito (`http` frente a `https`, `localhost` frente a `127.0.0.1`, puerto).

## Si falta tiempo

Recorta el paso 3 de la demo a la decodificación del payload y el `401` por
caducidad, y el paso 6 a una sola ejecución. No recortes los pasos 1, 2 y 5: son
el requisito previo de la práctica.
