"""S10.2 — Autenticación con API key: sin clave válida, 401."""

import logging
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from support import FRONT_KEY, OPS_KEY, build_settings

from wine_api.schemas import ErrorResponse


def assert_unauthorized(response) -> None:
    assert response.status_code == 401
    body = response.json()
    ErrorResponse.model_validate(body)
    assert body["error"]["code"] == "unauthorized"
    assert response.headers["WWW-Authenticate"] == "ApiKey"
    assert response.headers["X-Request-Id"] == body["request_id"]


def test_missing_key_returns_401_and_health_stays_public(
    anonymous_client: TestClient, valid_payload: dict
) -> None:
    assert anonymous_client.get("/health").status_code == 200

    response = anonymous_client.post("/v1/predictions", json=valid_payload)

    assert_unauthorized(response)


@pytest.mark.parametrize(
    "api_key",
    [
        "not-a-key",
        FRONT_KEY[:-1],
        FRONT_KEY.upper(),
        "clave-ñ".encode(),
    ],
    ids=["unknown", "prefix", "case", "non-ascii"],
)
def test_wrong_key_returns_401(
    anonymous_client: TestClient, valid_payload: dict, api_key: str | bytes
) -> None:
    response = anonymous_client.post(
        "/v1/predictions", json=valid_payload, headers={"X-API-Key": api_key}
    )

    assert_unauthorized(response)


def test_only_configured_clients_are_accepted(
    client: TestClient,
    ops_client: TestClient,
    anonymous_client: TestClient,
    valid_payload: dict,
) -> None:
    assert client.post("/v1/predictions", json=valid_payload).status_code == 200
    assert ops_client.post("/v1/predictions", json=valid_payload).status_code == 200
    unknown = anonymous_client.post(
        "/v1/predictions", json=valid_payload, headers={"X-API-Key": "unknown"}
    )
    assert unknown.status_code == 401


def test_no_clients_configured_fails_closed(
    make_client: Callable[..., TestClient], valid_payload: dict
) -> None:
    unconfigured = make_client(build_settings(clients={}))

    response = unconfigured.post("/v1/predictions", json=valid_payload)

    assert_unauthorized(response)


def test_api_keys_never_appear_in_responses_or_logs(
    anonymous_client: TestClient,
    client: TestClient,
    valid_payload: dict,
    caplog: pytest.LogCaptureFixture,
) -> None:
    attempted = "attempted-secret-key-0123"
    caplog.set_level(logging.DEBUG)

    rejected = anonymous_client.post(
        "/v1/predictions", json=valid_payload, headers={"X-API-Key": attempted}
    )
    accepted = client.post("/v1/predictions", json=valid_payload)

    assert rejected.status_code == 401
    assert accepted.status_code == 200
    for response in (rejected, accepted):
        exposed = response.text + str(response.headers)
        for secret in (attempted, FRONT_KEY, OPS_KEY):
            assert secret not in exposed
    for secret in (attempted, FRONT_KEY, OPS_KEY):
        assert secret not in caplog.text
