"""S9.4 (regresión) — Tests de referencia de S9.

El snapshot de OpenAPI se ha movido a `test_s10_6_openapi.py`: en S10 el
contrato cambia a propósito y se versiona como 2.0.0.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from wine_api.dependencies import get_predictor
from wine_api.predictor import UnavailablePredictor


@pytest.fixture
def unavailable_client(client: TestClient) -> Iterator[TestClient]:
    client.app.dependency_overrides[get_predictor] = UnavailablePredictor
    yield client
    client.app.dependency_overrides.clear()


@pytest.mark.parametrize("path", ["/health"])
def test_health_returns_503_when_model_is_unavailable(
    unavailable_client: TestClient, path: str
) -> None:
    response = unavailable_client.get(path)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_unavailable"


def test_prediction_returns_503_when_model_is_unavailable(
    unavailable_client: TestClient, valid_payload: dict
) -> None:
    response = unavailable_client.post("/v1/predictions", json=valid_payload)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "model_unavailable"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("alcohol", 4.99),
        ("alcohol", 20.01),
        ("ph", 2.49),
        ("density", 1.02),
        ("chlorides", -0.1),
        ("sulphates", None),
    ],
)
def test_out_of_contract_values_are_rejected(
    client: TestClient, valid_payload: dict, field: str, value: object
) -> None:
    valid_payload["features"][field] = value

    response = client.post("/v1/predictions", json=valid_payload)

    assert response.status_code == 422
    fields = [f["field"] for f in response.json()["error"]["fields"]]
    assert fields == [f"features.{field}"]


@pytest.mark.parametrize(("field", "value"), [("alcohol", 5), ("alcohol", 20)])
def test_range_limits_are_inclusive(
    client: TestClient, valid_payload: dict, field: str, value: float
) -> None:
    valid_payload["features"][field] = value

    assert client.post("/v1/predictions", json=valid_payload).status_code == 200


def test_raw_score_never_leaks(client: TestClient, valid_payload: dict) -> None:
    response = client.post("/v1/predictions", json=valid_payload)

    assert "raw_score" not in response.text
