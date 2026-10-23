"""S10.6 — Contrato 2.0.0: seguridad documentada y snapshot versionado."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wine_api.export_openapi import render_openapi

CONTRACT_PATH = Path(__file__).parents[1] / "contracts" / "openapi.json"
ERROR_REF = "#/components/schemas/ErrorResponse"


@pytest.fixture
def openapi(client: TestClient) -> dict:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    return response.json()


def api_key_schemes(openapi: dict) -> set[str]:
    schemes = openapi.get("components", {}).get("securitySchemes", {})
    return {
        name
        for name, scheme in schemes.items()
        if scheme.get("type") == "apiKey"
        and scheme.get("in") == "header"
        and scheme.get("name") == "X-API-Key"
    }


def test_version_is_2_0_0(openapi: dict) -> None:
    # Exigir autenticación rompe a los clientes anónimos de 1.x: cambio mayor.
    assert openapi["info"]["version"] == "2.0.0"


def test_api_key_scheme_is_declared_and_health_stays_public(openapi: dict) -> None:
    assert api_key_schemes(openapi) == {"APIKeyHeader"}
    assert "security" not in openapi["paths"]["/health"]["get"]


@pytest.mark.parametrize(
    ("method", "path"), [("post", "/v1/predictions"), ("get", "/v1/admin/usage")]
)
def test_protected_operations_require_the_api_key(
    openapi: dict, method: str, path: str
) -> None:
    operation = openapi["paths"][path][method]

    assert operation.get("security") == [{"APIKeyHeader": []}]


@pytest.mark.parametrize(
    ("method", "path", "statuses"),
    [
        ("post", "/v1/predictions", ("401", "403", "429")),
        ("get", "/v1/admin/usage", ("401", "403")),
    ],
)
def test_protected_operations_document_security_errors(
    openapi: dict, method: str, path: str, statuses: tuple[str, ...]
) -> None:
    responses = openapi["paths"][path][method]["responses"]

    for status in statuses:
        schema = responses[status]["content"]["application/json"]["schema"]
        assert schema["$ref"] == ERROR_REF, status


def test_429_documents_retry_after(openapi: dict) -> None:
    response = openapi["paths"]["/v1/predictions"]["post"]["responses"]["429"]

    assert "Retry-After" in response.get("headers", {})


def test_admin_tag_and_security_error_codes_are_documented(openapi: dict) -> None:
    tags = {tag["name"]: tag.get("description") for tag in openapi.get("tags", [])}
    assert tags.get("admin")
    codes = set(openapi["components"]["schemas"]["ErrorCode"]["enum"])
    assert {"unauthorized", "forbidden", "rate_limited"} <= codes


def test_openapi_matches_versioned_contract() -> None:
    """Si falla, regenera con `uv run python -m wine_api.export_openapi`."""

    committed = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert committed["info"]["version"] == "2.0.0"
    assert json.loads(render_openapi()) == committed
