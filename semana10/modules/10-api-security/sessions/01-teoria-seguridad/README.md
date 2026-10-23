# Clase 1 — Teoría y demo: API protegida (2 h)

## Objetivo

Entender qué le falta a una API documentada y testeada para exponerla fuera del
portátil: saber quién llama, qué puede hacer, desde qué páginas web se la puede
leer, cuánto puede consumir y dónde viven los secretos. Cerrar con una demo en
vivo que lo enseña funcionando y lo mide con Locust.

## Secuencia

| Tiempo | Bloque | Diapositivas | Demo |
| ---: | --- | --- | --- |
| 10 min | Introducción | 1–5 | — |
| 25 min | 1 · Autenticación | 6–11 | `examples/api_key_demo.py` (fragmento A) |
| 25 min | 2 · Autorización y JWT | 12–17 | `examples/api_key_demo.py` (fragmento B), `examples/jwt_demo.py` |
| 15 min | 3 · CORS | 18–21 | `examples/cors_demo.py` |
| 15 min | 4 · Secretos, límites y carga | 22–27 | `examples/limits_demo.py`, `examples/locustfile.py` |
| 30 min | Demo en vivo y resumen | 28–30 | Las cinco anteriores, en seis pasos |

La teoría (1 h 30) usa fragmentos de las demos, no de la solución de la
práctica, para no adelantar los TODO. La demo en vivo (30 min) sigue el guion de
la diapositiva 29 y de la [guía de la clase 1](../../guides/class-1-theory-demo.md).

## Guion de la demo en vivo

| Paso | Min | Qué se ve | Archivo |
| --- | ---: | --- | --- |
| 1 | 5 | Sin clave → `401` con `WWW-Authenticate`; clave `front` → `200` | `api_key_demo.py` |
| 2 | 5 | `front` en `/v1/admin/usage` → `403`; `ops` → `200` | `api_key_demo.py` |
| 3 | 5 | Emitir y validar un JWT; caducado u otra audiencia → `401` | `jwt_demo.py` |
| 4 | 5 | Preflight CORS con origen permitido (`200`) y no permitido (`400`) | `cors_demo.py` |
| 5 | 5 | Bucle de peticiones → `429` con `Retry-After` | `limits_demo.py` |
| 6 | 5 | Locust con 20 usuarios: RPS, p95 y porcentaje de `429` | `locustfile.py` |

## Preparación del docente

Desde `semana10/modules/10-api-security`:

```bash
uv sync --locked --group load
uv run pytest -q
```

Debe mostrar `19 passed`. Ten dos terminales abiertas en la raíz del módulo (API
y cliente) y `jq` instalado para el paso 3; si no lo tienes, copia el token a
mano.

## Resultado esperado

Al terminar, el alumnado sabe explicar con sus palabras:

- la diferencia entre autenticación (`401`) y autorización (`403`);
- por qué una API key se compara con `compare_digest` y nunca viaja en la URL;
- qué valida una API al recibir un JWT y por qué su contenido no es secreto;
- qué protege CORS y qué no;
- por qué la configuración se valida al arrancar y los secretos no van al
  repositorio;
- qué significa un `429` con `Retry-After` y qué mide una prueba de carga.

## Antes de la clase 2

Pide que cada persona ejecute en el starter de la práctica:

```bash
cd exercises/01-wine-api-security/problem/starter
uv sync --locked --group load
uv run pytest -q
```

Resultado esperado: `44 failed, 34 passed`.
