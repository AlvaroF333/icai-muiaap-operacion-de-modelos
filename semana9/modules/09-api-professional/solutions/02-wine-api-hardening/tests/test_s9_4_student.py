"""S9.4 — Tests escritos por el alumnado (versión de referencia)."""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from wine_api.dependencies import get_predictor
from wine_api.export_openapi import render_openapi
from wine_api.main import create_app
from wine_api.predictor import DemoWinePredictor, UnavailablePredictor

CONTRACT_PATH = Path(__file__).parents[1] / "contracts" / "openapi.json"


@pytest.fixture
def unavailable_client() -> Iterator[TestClient]:
    app = create_app(predictor=DemoWinePredictor())
    app.dependency_overrides[get_predictor] = UnavailablePredictor
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


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


def test_openapi_matches_versioned_contract() -> None:
    """Si falla, regenera con `uv run python -m wine_api.export_openapi`."""

    committed = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert json.loads(render_openapi()) == committed
