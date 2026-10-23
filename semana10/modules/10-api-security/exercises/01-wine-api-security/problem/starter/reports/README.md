# S10.7 — Informe de carga

> **TODO S10.7c:** ejecuta Locust con `--csv reports/s10`, versiona los CSV
> generados y completa las tablas y el análisis de este archivo.

Plantilla del informe. Rellénala con **tus** resultados: dependen de la máquina,
del número de workers y de la configuración de `.env`. No copies cifras de otra
persona ni de la solución, que no incluye resultados.

## Cómo se ha medido

| Dato | Valor |
| --- | --- |
| Comando de la API | `uv run fastapi dev` (1 proceso) |
| Comando de Locust | `uv run --group load locust -f locustfile.py --headless -u 20 -r 5 -t 1m --host http://127.0.0.1:8000 --csv reports/s10` |
| Cliente usado | _p. ej. `front`_ |
| `rate_limit_per_minute` del cliente | _p. ej. 60_ |
| Máquina | _CPU, sistema operativo_ |

Archivos generados por Locust y versionados junto a este informe:
`s10_stats.csv`, `s10_failures.csv` y `s10_stats_history.csv`.

## Resultados

Copia los valores de la fila `POST /v1/predictions` y de `Aggregated` de
`s10_stats.csv`.

| Endpoint | Peticiones | RPS | p50 (ms) | p95 (ms) | Fallos | % 429 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `POST /v1/predictions` | | | | | | |
| `/v1/predictions [422]` | | | | | | — |
| `GET /health` | | | | | | — |
| Aggregated | | | | | | |

`% 429` = fallos `429` de `s10_failures.csv` / peticiones de
`POST /v1/predictions` × 100.

## Análisis (5–10 líneas)

- ¿Cuántas predicciones por minuto deja pasar el límite y cuántas ha pedido
  Locust? ¿Cuadra el `% 429` con esa cuenta?
- ¿Qué latencia (p50, p95) tiene `GET /health`, que no pasa por autenticación ni
  rate limit, frente a `POST /v1/predictions`?
- ¿Qué cambiaría con dos workers (`fastapi run --workers 2`) y un contador en
  memoria por proceso?
- Si quisieras medir la capacidad del servicio y no la política de cuotas, ¿qué
  cliente y qué límite usarías?
