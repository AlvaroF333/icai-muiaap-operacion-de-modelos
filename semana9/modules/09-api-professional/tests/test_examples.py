"""Demo S9 · Bloque 4 — Pruebo comportamiento, no implementación.

Estos tests son a la vez la comprobación de las demos y el ejemplo que se
proyecta en clase: `uv run pytest -q` desde la raíz del módulo.
"""

from collections.abc import Iterator

import errors_demo
import openapi_demo
import pytest
import serialization_demo
from fastapi.testclient import TestClient


@pytest.fixture
def errors_client() -> Iterator[TestClient]:
    with TestClient(errors_demo.app, raise_server_exceptions=False) as client:
        yield client
    errors_demo.app.dependency_overrides.clear()


def test_leaky_endpoint_exposes_internal_fields() -> None:
    client = TestClient(serialization_demo.app)

    body = client.get("/v1/scores/leaky").json()

    assert "raw_score" in body
    assert "threshold_config" in body


@pytest.mark.parametrize("path", ["/v1/scores/public", "/v1/scores/filtered"])
def test_public_endpoints_filter_and_serialize(path: str) -> None:
    client = TestClient(serialization_demo.app)

    body = client.get(path).json()

    assert "raw_score" not in body
    assert body["confidence"] == 0.83
    assert body["served_at"].endswith("Z")
    assert body["is_reliable"] is True


def test_exclude_none_drops_empty_fields() -> None:
    client = TestClient(serialization_demo.app)

    assert "note" not in client.get("/v1/scores/compact").json()
    assert client.get("/v1/scores/public").json()["note"] is None


def test_validation_error_uses_the_envelope(errors_client: TestClient) -> None:
    response = errors_client.post("/v1/scores", json={"age": "treinta", "income": 1})

    assert response.status_code == 422
    assert response.json()["error"]["fields"][0]["field"] == "age"


def test_unknown_route_uses_the_envelope(errors_client: TestClient) -> None:
    response = errors_client.get("/v1/nothing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_unexpected_error_hides_secrets(errors_client: TestClient) -> None:
    response = errors_client.get("/v1/boom")

    assert response.status_code == 500
    assert "TU_SECRETO" not in response.text


def test_dependency_override_simulates_unavailable_model(
    errors_client: TestClient,
) -> None:
    broken = errors_demo.Model()
    broken.ready = False
    errors_demo.app.dependency_overrides[errors_demo.get_model] = lambda: broken

    response = errors_client.post("/v1/scores", json={"age": 30, "income": 1000})

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_unavailable"


def test_openapi_documents_errors_and_examples() -> None:
    schema = TestClient(openapi_demo.app).get("/openapi.json").json()
    operation = schema["paths"]["/v1/scores"]["post"]

    assert operation["summary"] == "Calcular el score de riesgo"
    assert "impago" in operation["description"]
    error_ref = operation["responses"]["422"]["content"]["application/json"]
    assert error_ref["schema"]["$ref"].endswith("ErrorResponse")
    examples = operation["requestBody"]["content"]["application/json"]["examples"]
    assert set(examples) == {"valid", "minor"}
