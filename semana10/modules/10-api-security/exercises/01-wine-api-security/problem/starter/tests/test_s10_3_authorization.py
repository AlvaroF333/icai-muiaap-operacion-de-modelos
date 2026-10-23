"""S10.3 — Autorización por scopes y `GET /v1/admin/usage`."""

from collections.abc import Callable

from fastapi.testclient import TestClient
from support import FRONT_KEY, OPS_KEY, build_settings, client_config


def assert_forbidden(response) -> None:
    assert response.status_code == 403
    body = response.json()
    assert body["error"]["code"] == "forbidden"
    assert response.headers["X-Request-Id"] == body["request_id"]


def test_front_cannot_read_admin_usage(client: TestClient) -> None:
    assert_forbidden(client.get("/v1/admin/usage"))


def test_admin_usage_requires_authentication(anonymous_client: TestClient) -> None:
    response = anonymous_client.get("/v1/admin/usage")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthorized"


def test_ops_reads_usage_of_every_client(ops_client: TestClient) -> None:
    response = ops_client.get("/v1/admin/usage")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"clients", "request_id"}
    assert response.headers["X-Request-Id"] == body["request_id"]
    assert [entry["client"] for entry in body["clients"]] == ["front", "ops"]
    for entry in body["clients"]:
        assert set(entry) == {"client", "requests_in_window", "limit"}
        assert entry["requests_in_window"] >= 0
        assert entry["limit"] == 1_000


def test_usage_never_exposes_keys(ops_client: TestClient) -> None:
    response = ops_client.get("/v1/admin/usage")

    assert response.status_code == 200
    assert FRONT_KEY not in response.text
    assert OPS_KEY not in response.text
    assert "key" not in response.text


def test_client_without_predict_scope_cannot_predict(
    make_client: Callable[..., TestClient], valid_payload: dict
) -> None:
    auditor_key = "test-auditor-key-not-for-production"
    settings = build_settings(
        clients={"auditor": client_config(auditor_key, ["admin"])}
    )
    auditor = make_client(settings, api_key=auditor_key)

    assert_forbidden(auditor.post("/v1/predictions", json=valid_payload))
    assert auditor.get("/v1/admin/usage").status_code == 200
