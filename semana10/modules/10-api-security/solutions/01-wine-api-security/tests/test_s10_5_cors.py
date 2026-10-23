"""S10.5 — CORS desde la configuración y documentación desactivable."""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from support import build_settings

FRONT_ORIGIN = "http://localhost:8501"


def preflight(origin: str) -> dict[str, str]:
    return {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,x-api-key",
    }


def test_preflight_from_the_front_is_allowed_without_api_key(
    anonymous_client: TestClient,
) -> None:
    response = anonymous_client.options(
        "/v1/predictions", headers=preflight(FRONT_ORIGIN)
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == FRONT_ORIGIN
    assert "x-api-key" in response.headers["access-control-allow-headers"].lower()
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "access-control-allow-credentials" not in response.headers


def test_preflight_from_an_unknown_origin_is_rejected(
    anonymous_client: TestClient,
) -> None:
    response = anonymous_client.options(
        "/v1/predictions", headers=preflight("https://evil.example")
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_browser_can_read_operational_headers(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": FRONT_ORIGIN})

    assert response.headers["access-control-allow-origin"] == FRONT_ORIGIN
    exposed = response.headers["access-control-expose-headers"].lower()
    for header in ("x-request-id", "retry-after", "x-ratelimit-remaining"):
        assert header in exposed


def test_allowed_origins_come_from_settings(
    make_client: Callable[..., TestClient],
) -> None:
    custom = make_client(build_settings(cors_origins=["https://wine.example"]))

    allowed = custom.options(
        "/v1/predictions", headers=preflight("https://wine.example")
    )
    default = custom.options("/v1/predictions", headers=preflight(FRONT_ORIGIN))

    assert allowed.status_code == 200
    assert default.status_code == 400


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_docs_follow_settings(
    make_client: Callable[..., TestClient], path: str
) -> None:
    enabled = make_client(build_settings(docs_enabled=True))
    disabled = make_client(build_settings(docs_enabled=False))

    assert enabled.get(path).status_code == 200
    assert disabled.get(path).status_code == 404
