# Semana 7 — Solución práctica Requests + AEMET

Enunciado: [../../AEMET/enunciado_aemet.pdf](../../AEMET/enunciado_aemet.pdf)

Objetivo: usando `requests`, obtener la **climatología diaria de octubre de
2019** en la estación **MADRID, CIUDAD UNIVERSITARIA** a través de la API de
AEMET OpenData.

## Cómo ejecutarlo

```bash
cd semana7/modules/Solucion-semana7-AEMET
cp .env.example .env          # y pega tu API key en API_AEMET=
uv sync                       # crea .venv con requests, python-dotenv, pandas
uv run python -m solucion_semana7_aemet
uv run pytest -q              # tests sin red (requests simulado)
```

La salida queda en `data/`:

- `climatologia_diaria_<idema>_2019-10-01_2019-10-30.json` — respuesta cruda.
- `climatologia_diaria_<idema>_2019-10-01_2019-10-30.csv` — tabla limpia.

## Flujo HTTP

AEMET responde **en dos pasos**: el endpoint devuelve un "sobre" JSON con una
URL temporal en `datos`, y hay que hacer un segundo GET a esa URL.

```
GET /api/valores/climatologicos/inventarioestaciones/todasestaciones?api_key=…
  -> {"estado":200, "datos":"https://…/sh/…"}  -> GET datos -> [ {indicativo, nombre, …}, … ]
     buscar nombre == "MADRID, CIUDAD UNIVERSITARIA"  -> indicativo (idema) = 3194U

GET /api/valores/climatologicos/diarios/datos/fechaini/2019-10-01T00:00:00UTC
    /fechafin/2019-10-30T23:59:59UTC/estacion/3194U?api_key=…
  -> {"estado":200, "datos":"https://…"}  -> GET datos -> [ {fecha, tmed, tmax, prec, …}, … ]
```

## Estructura

| Fichero | Qué hace |
| --- | --- |
| `src/solucion_semana7_aemet/client.py` | `AemetClient`: API key en query string, timeout, reintentos ante 429/5xx, validación del sobre (`estado`) y descarga de `datos` con codificación ISO-8859-15. |
| `src/solucion_semana7_aemet/transform.py` | Convierte los valores de texto con coma decimal (`"15,2"`, `"Ip"`) a números y fechas. |
| `src/solucion_semana7_aemet/__main__.py` | Orquesta los pasos del enunciado y guarda JSON + CSV. |
| `tests/test_client.py` | Tests de contrato sin red: dos pasos, `api_key` en query, errores 401/404, reintento 429, parseo. |

## Decisiones y detalles

- **Secretos fuera del código:** la API key se lee de `.env` (ignorado por git);
  se versiona solo `.env.example`.
- **El código HTTP no basta:** AEMET puede devolver HTTP 200 con
  `"estado": 404` ("No hay datos que satisfagan esos criterios"). Por eso se
  valida también el campo `estado` del sobre.
- **Codificación:** los ficheros de `datos` vienen en ISO-8859-15; si no se
  fuerza, los nombres con tildes salen corruptos.
- **Fechas:** se respetan las del enunciado (fin el 30 de octubre). Para el mes
  completo: `--fecha-fin 2019-10-31T23:59:59UTC`.
- **Rate limit:** AEMET limita peticiones por minuto; ante 429 se reintenta con
  espera creciente.
