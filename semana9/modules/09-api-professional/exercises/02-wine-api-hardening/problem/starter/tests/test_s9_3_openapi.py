"""S9.3 — El contrato OpenAPI documenta lo que la API hace de verdad."""

import pytest
from fastapi.testclient import TestClient

ERROR_REF = "#/components/schemas/ErrorResponse"


@pytest.fixture
def openapi(client: TestClient) -> dict:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    return response.json()


def operations(openapi: dict):
    for path, item in openapi["paths"].items():
        for method, operation in item.items():
            yield f"{method.upper()} {path}", operation


def test_info_describes_the_service(openapi: dict) -> None:
    info = openapi["info"]
    assert info["title"] == "Wine Quality API"
    assert info["version"] == "1.1.0"
    assert info.get("summary")
    assert "request_id" in info.get("description", "")


def test_tags_are_declared_with_descriptions(openapi: dict) -> None:
    tags = {tag["name"]: tag.get("description") for tag in openapi.get("tags", [])}
    assert set(tags) == {"health", "predictions"}
    assert all(tags.values())


def test_every_operation_has_summary_docstring_and_tag(openapi: dict) -> None:
    for name, operation in operations(openapi):
        assert operation.get("summary"), name
        assert len(operation.get("description", "")) > 40, name
        assert len(operation.get("tags", [])) == 1, name


def test_prediction_errors_reference_the_error_envelope(openapi: dict) -> None:
    responses = openapi["paths"]["/v1/predictions"]["post"]["responses"]

    for status in ("400", "422", "503"):
        schema = responses[status]["content"]["application/json"]["schema"]
        assert schema["$ref"] == ERROR_REF, status
    assert "HTTPValidationError" not in openapi["components"]["schemas"]


def test_health_documents_503(openapi: dict) -> None:
    responses = openapi["paths"]["/health"]["get"]["responses"]
    schema = responses["503"]["content"]["application/json"]["schema"]
    assert schema["$ref"] == ERROR_REF


def test_request_body_offers_valid_and_invalid_examples(openapi: dict) -> None:
    body = openapi["paths"]["/v1/predictions"]["post"]["requestBody"]
    examples = body["content"]["application/json"]["examples"]
    assert "valid" in examples
    assert len(examples) >= 3


def test_feature_fields_are_described(openapi: dict) -> None:
    properties = openapi["components"]["schemas"]["WineFeatures"]["properties"]
    assert len(properties) == 11
    for name, field in properties.items():
        assert field.get("description"), name
        assert "minimum" in field and "maximum" in field, name
