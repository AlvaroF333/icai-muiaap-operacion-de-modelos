# Diapositivas — Semana 10 · API protegida

Deck de 37 diapositivas para las dos clases de 2 horas, con la plantilla
«Diapositivas Comillas ICAI» del MUIAAp. Cada diapositiva lleva notas del
ponente con guion, tiempos, preguntas y el archivo de demo que hay que abrir.

- **Deck editable:** <https://claude.ai/artifact/MFDZ1JeCdE4v5HUGspyQxv>
  (privado hasta que se comparta desde su menú Share; desde ahí se exporta a
  PDF o PPTX).
- **Fuente versionada:** [`deck/`](deck/) contiene el índice `deck.json` y una
  `section` HTML por diapositiva. Es una copia de la versión publicada para
  revisar cambios en Git; la fuente de verdad para editar es el deck enlazado.

## Estructura

| Diapositivas | Clase | Bloque | Tiempo |
| ---: | --- | --- | ---: |
| 1–5 | 1 · Teoría | Introducción: quién llama, cuántas veces y desde dónde | 10 min |
| 6–11 | 1 · Teoría | Autenticación: API key en cabecera, `compare_digest` y 401 | 25 min |
| 12–17 | 1 · Teoría | Autorización: scopes en el `APIRouter`, 403 y JWT Bearer | 25 min |
| 18–21 | 1 · Teoría | CORS: qué protege, preflight y configuración explícita | 15 min |
| 22–27 | 1 · Teoría | Secrets con pydantic-settings, rate limiting, Locust y OWASP | 15 min |
| 28–30 | 1 · Demo | Demo en vivo en seis pasos y resumen de la clase | 30 min |
| 31–37 | 2 · Práctica | Starter, plan S10.1–S10.7, configuración, carga, criterios y entregable | 120 min |

Las demos que se proyectan están en
[`modules/10-api-security/examples`](../modules/10-api-security/examples/README.md)
y la práctica en
[`exercises/01-wine-api-security`](../modules/10-api-security/exercises/01-wine-api-security/README.md).
El código de las diapositivas de teoría procede de las demos, no de la solución
de la práctica, para no adelantar los TODO. Las claves que aparecen son
marcadores (`TU_API_KEY`, `cambia-esta-clave-front`) o claves de demo marcadas
como tales, nunca credenciales reales.
