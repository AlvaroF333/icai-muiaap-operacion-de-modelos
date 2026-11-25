# S10.7 — Informe de carga

Resultados de una ejecución de 1 minuto el 2026-11-25. Dependen de la máquina,
del número de workers y de la configuración de `.env`.

## Cómo se ha medido

| Dato | Valor |
| --- | --- |
| Comando de la API | `uv run uvicorn wine_api.main:app --port 8000` (1 proceso) |
| Comando de Locust | `uv run --group load locust -f locustfile.py --headless -u 20 -r 5 -t 1m --host http://127.0.0.1:8000 --csv reports/s10` |
| Cliente usado | `front` (scope `predict`), clave en `LOCUST_API_KEY` |
| `rate_limit_per_minute` del cliente | 60 |
| Máquina | Intel Core i7-1255U, Windows 11 Home |

Archivos generados por Locust y versionados junto a este informe:
`s10_stats.csv`, `s10_failures.csv`, `s10_stats_history.csv` y
`s10_exceptions.csv` (vacío).

## Resultados

Valores de `s10_stats.csv` y `s10_failures.csv`.

| Endpoint | Peticiones | RPS | p50 (ms) | p95 (ms) | Fallos | % 429 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `POST /v1/predictions` | 673 | 12.33 | 9 | 23 | 618 | 91.8 % |
| `/v1/predictions [422]` | 77 | 1.41 | 9 | 21 | 72 | — |
| `GET /health` | 85 | 1.56 | 6 | 17 | 0 | — |
| Aggregated | 835 | 15.30 | 9 | 21 | 690 | — |

`% 429` = 618 fallos `429` / 673 peticiones de `POST /v1/predictions` × 100.
Los 72 fallos de la fila `[422]` también son `429` (`expected 422, got 429`).

## Análisis

- El límite deja pasar 60 predicciones por minuto al cliente `front` y Locust
  ha pedido 750 (673 válidas + 77 inválidas). Han pasado 55 válidas y 5
  inválidas: exactamente 60. El resto, un 92 % del total, recibió `429`, así
  que la cuenta cuadra con la cuota.
- Las peticiones inválidas también consumen cuota: el rate limit es una
  dependencia del router y se resuelve antes de validar el cuerpo. Por eso,
  agotada la cuota, el payload inválido recibe `429` en vez de `422`.
- `GET /health` (sin autenticación ni cuota) tiene p50 6 ms y p95 17 ms, frente
  a 9 ms y 23 ms de `POST /v1/predictions`. La diferencia es pequeña porque casi
  todas las predicciones se cortan en el `429` sin llegar al modelo.
- Con dos workers (`--workers 2`), cada proceso tendría su propio contador en
  memoria y el cliente podría hacer hasta 120 peticiones por minuto. Para una
  cuota global haría falta un contador compartido (por ejemplo, Redis).
- Para medir la capacidad del servicio, y no la política de cuotas, usaría un
  cliente de pruebas con un `rate_limit_per_minute` muy alto (por ejemplo,
  100 000), de modo que el límite nunca se alcance.
