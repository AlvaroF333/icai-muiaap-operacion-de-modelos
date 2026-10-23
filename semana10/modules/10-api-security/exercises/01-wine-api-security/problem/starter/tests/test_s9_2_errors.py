"""S9.2 (regresión) — Todos los errores comparten un sobre predecible."""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from wine_api.predictor import ModelOutput
from wine_api.schemas import ErrorResponse, WineFeatures


def assert_error_envelope(response, status_code: int, code: str) -> dict:
    assert response.status_code == status_code
    body = response.json()
    ErrorResponse.model_validate(body)
    assert body["error"]["code"] == code
    assert response.headers["X-Request-Id"] == body["request_id"]
    return body


def test_wrong_type_returns_422_with_field_path(
    client: TestClient, valid_payload: dict
) -> None:
    valid_payload["features"]["alcohol"] = "mucho"

    response = client.post("/v1/predictions", json=valid_payload)

    body = assert_error_envelope(response, 422, "validation_error")
    assert [f["field"] for f in body["error"]["fields"]] == ["features.alcohol"]


def test_booleans_are_not_numbers(client: TestClient, valid_payload: dict) -> None:
    valid_payload["features"]["density"] = True

    response = client.post("/v1/predictions", json=valid_payload)

    body = assert_error_envelope(response, 422, "validation_error")
    assert body["error"]["fields"][0]["field"] == "features.density"


def test_extra_and_missing_fields_are_reported(
    client: TestClient, valid_payload: dict
) -> None:
    del valid_payload["features"]["ph"]
    valid_payload["features"]["color"] = "red"

    response = client.post("/v1/predictions", json=valid_payload)

    body = assert_error_envelope(response, 422, "validation_error")
    fields = {f["field"] for f in body["error"]["fields"]}
    assert fields == {"features.ph", "features.color"}


def test_malformed_json_returns_400(client: TestClient) -> None:
    response = client.post(
        "/v1/predictions",
        content=b'{"features": ',
        headers={"Content-Type": "application/json"},
    )

    body = assert_error_envelope(response, 400, "invalid_json")
    assert "fields" not in body["error"]


def test_unknown_route_uses_the_same_envelope(client: TestClient) -> None:
    response = client.get("/v1/unknown")

    assert_error_envelope(response, 404, "not_found")


def test_wrong_method_uses_the_same_envelope(client: TestClient) -> None:
    response = client.get("/v1/predictions")

    assert_error_envelope(response, 405, "method_not_allowed")


class ExplodingPredictor:
    model_version = "broken"

    def is_ready(self) -> bool:
        return True

    def predict(self, features: WineFeatures) -> ModelOutput:
        raise RuntimeError("secret at /srv/models/wine.joblib")


@pytest.fixture
def exploding_client(make_client: Callable[..., TestClient]) -> TestClient:
    return make_client(predictor=ExplodingPredictor())


def test_unexpected_error_hides_internal_details(
    exploding_client: TestClient, valid_payload: dict
) -> None:
    response = exploding_client.post("/v1/predictions", json=valid_payload)

    assert_error_envelope(response, 500, "internal_error")
    assert "secret" not in response.text
    assert "Traceback" not in response.text


def test_error_never_echoes_the_payload(
    client: TestClient, valid_payload: dict
) -> None:
    valid_payload["features"]["alcohol"] = "token-do-not-echo"

    response = client.post("/v1/predictions", json=valid_payload)

    assert response.status_code == 422
    assert "token-do-not-echo" not in response.text
