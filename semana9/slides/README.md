# Diapositivas — Semana 9 · API profesional

Deck de 35 diapositivas para las dos clases de 2 horas, con la plantilla
«Diapositivas Comillas ICAI» del MUIAAp. Cada diapositiva lleva notas del
ponente con guion, tiempos y preguntas.

- **Deck editable:** <https://claude.ai/artifact/5CZPntT6wj9U7DVGfuui7J>
  (privado hasta que se comparta desde su menú Share; desde ahí se exporta a
  PDF o PPTX).
- **Fuente versionada:** [`deck/`](deck/) contiene el índice `deck.json` y una
  `section` HTML por diapositiva. Es una copia de la versión publicada para
  revisar cambios en Git; la fuente de verdad para editar es el deck enlazado.

## Estructura

| Diapositivas | Clase | Bloque | Tiempo |
| ---: | --- | --- | ---: |
| 1–5 | 1 · Teoría | Introducción: de una API que funciona a una mantenible | 10 min |
| 6–12 | 1 · Teoría | Serialización: la respuesta también es un contrato | 30 min |
| 13–18 | 1 · Teoría | Errores: un único sobre, códigos estables y nada interno | 30 min |
| 19–23 | 1 · Teoría | OpenAPI: metadatos, docstrings, `responses` y ejemplos | 25 min |
| 24–29 | 1 · Teoría | Tests: `TestClient`, overrides, snapshot y resumen | 25 min |
| 30–35 | 2 · Workshop | Starter, plan, comandos, criterios y entregable | 120 min |

Las demos que se proyectan están en
[`modules/09-api-professional/examples`](../modules/09-api-professional/examples/README.md)
y el workshop en
[`exercises/02-wine-api-hardening`](../modules/09-api-professional/exercises/02-wine-api-hardening/README.md).
El código de las diapositivas de teoría procede de las demos, no de la solución
del workshop, para no adelantar los TODO.
