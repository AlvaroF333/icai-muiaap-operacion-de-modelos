# Solución comentada — Microejercicios de la clase 1

Referencia docente para el cierre de cada bloque. Compártela después de que el
grupo haya intentado el microejercicio.

## M1 — Serialización

1. `/v1/scores/leaky` devuelve también `raw_score` y `threshold_config`, que es
   una ruta interna del servidor.
2. `/v1/scores/filtered` declara `response_model=PublicScore`: FastAPI valida el
   `dict` contra ese modelo y serializa solo los campos declarados. Lo que no
   está en el modelo público se descarta.
3. Sí. `@computed_field` se incluye en la serialización y en el esquema de
   respuesta de OpenAPI.

## M2 — Errores

| Petición | Status | `error.code` | `error.fields` |
| --- | ---: | --- | --- |
| Válida | 200 | — | — |
| `age: "treinta"` | 422 | `validation_error` | `[{"field": "age", ...}]` |
| Falta `income` | 422 | `validation_error` | `[{"field": "income", ...}]` |
| `GET /v1/nada` | 404 | `not_found` | — |
| `GET /v1/boom` | 500 | `internal_error` | — |

Sin `handle_validation`, FastAPI responde `{"detail": [{"type": ..., "loc":
["body", "age"], "msg": ..., "input": "treinta"}]}`: otra forma de error, y
además devuelve el `input` del usuario.

## M3 — OpenAPI

- `summary` → `paths./v1/scores.post.summary`.
- Docstring → `paths./v1/scores.post.description`, renderizado como Markdown.
- `responses` del router → `paths./v1/scores.post.responses.422` y `.503`, con
  `$ref` a `#/components/schemas/ErrorResponse`.

Ejemplo añadido:

```python
"no_income": {"summary": "Sin ingresos: 422", "value": {"age": 30}},
```

El test `test_openapi_documents_errors_and_examples` compara el conjunto exacto
de ejemplos; si se mantiene el tercero, hay que añadir `"no_income"` al conjunto
esperado.

## M4 — Tests

Sin `raise_server_exceptions=False`, `TestClient` relanza el `RuntimeError` de
`/v1/boom` dentro del test y `test_unexpected_error_hides_secrets` falla con la
excepción en lugar de recibir el `500`. Es útil para depurar, pero no prueba lo
que ve el cliente.

```python
def test_zero_income_is_rejected(errors_client: TestClient) -> None:
    response = errors_client.post("/v1/scores", json={"age": 30, "income": 0})

    assert response.status_code == 422
    assert response.json()["error"]["fields"][0]["field"] == "income"
```
