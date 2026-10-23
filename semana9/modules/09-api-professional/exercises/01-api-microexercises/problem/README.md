# Ejercicio 01 — Microejercicios de la clase 1

Cuatro microejercicios de 5 minutos, uno al final de cada bloque de teoría. Se
hacen sobre las demos de [`examples/`](../../../examples/README.md) y no
requieren escribir una API nueva.

Prepara el entorno una vez, desde `semana9/modules/09-api-professional`:

```bash
uv sync --locked
```

## M1 — Serialización (bloque 1)

Arranca `uv run fastapi dev examples/serialization_demo.py` y compara
`/v1/scores/leaky` con `/v1/scores/public`.

1. Anota qué campos aparecen en la primera respuesta y no en la segunda.
2. Explica en una frase por qué `/v1/scores/filtered` tampoco los devuelve,
   aunque la función devuelve un `dict` con todos ellos.
3. En `/docs`, abre el esquema `PublicScore`: ¿aparece `is_reliable`?

**Comprobación:** tu respuesta a la pregunta 2 menciona `response_model` y
qué hace con los campos que no declara.

## M2 — Errores (bloque 2)

Arranca `uv run fastapi dev examples/errors_demo.py` y envía, desde `/docs` o
con `curl`, tres peticiones a `POST /v1/scores`:

- `{"age": 30, "income": 1000}`
- `{"age": "treinta", "income": 1000}`
- `{"age": 30}`

Después llama a `GET /v1/nada` y a `GET /v1/boom`.

1. Rellena una tabla con status, `error.code` y `error.fields` de cada caso.
2. ¿Qué devolvería FastAPI en el segundo caso si borraras `handle_validation`?
   Pruébalo comentando el decorador y restáuralo después.

**Comprobación:** las cinco respuestas de error tienen la clave `error` en la
raíz y ninguna contiene el texto `TU_SECRETO`.

## M3 — OpenAPI (bloque 3)

Arranca `uv run fastapi dev examples/openapi_demo.py`.

1. Localiza en `/openapi.json` dónde terminan `summary`, el docstring y
   `responses` de `create_score`.
2. Ejecuta el ejemplo `minor` desde Swagger con «Try it out».
3. Añade un tercer ejemplo `no_income` sin el campo `income` y comprueba que
   aparece en el desplegable.

**Comprobación:** `uv run pytest -q` sigue en verde y el desplegable muestra
tres ejemplos. Deshaz el cambio al terminar o adapta el test que cuenta los
ejemplos.

## M4 — Tests (bloque 4)

Abre [`tests/test_examples.py`](../../../tests/test_examples.py).

1. Ejecuta `uv run pytest -q` y localiza el test que usa `dependency_overrides`.
2. Elimina temporalmente `raise_server_exceptions=False` del fixture
   `errors_client` y vuelve a ejecutar. Explica qué cambia.
3. Escribe un test nuevo que compruebe que `income: 0` devuelve `422` con
   `fields[0].field == "income"`.

**Comprobación:** la suite vuelve a estar en verde con tu test incluido.

La [solución comentada](../solution/README.md) se comparte al final de la clase.
