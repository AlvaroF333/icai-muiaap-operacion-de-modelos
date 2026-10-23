"""S9.1 (regresión) — La respuesta también es un contrato."""

from datetime import datetime

from fastapi.testclient import TestClient

from wine_api.schemas import PredictionResponse, QualityBand


def test_prediction_exposes_only_public_fields(
    client: TestClient, valid_payload: dict
) -> None:
    response = client.post("/v1/predictions", json=valid_payload)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"prediction", "request_id", "served_at"}
    assert set(body["prediction"]) == {
        "quality_band",
        "confidence",
        "model_version",
        "preprocessing_version",
    }


def test_prediction_body_validates_against_response_model(
    client: TestClient, valid_payload: dict
) -> None:
    body = client.post("/v1/predictions", json=valid_payload).json()

    parsed = PredictionResponse.model_validate(body)
    assert parsed.prediction.quality_band in set(QualityBand)


def test_confidence_is_serialized_with_two_decimals(
    client: TestClient, valid_payload: dict
) -> None:
    confidence = client.post("/v1/predictions", json=valid_payload).json()[
        "prediction"
    ]["confidence"]

    assert 0 <= confidence <= 1
    assert confidence == round(confidence, 2)


def test_served_at_is_utc_iso_8601_with_z(
    client: TestClient, valid_payload: dict
) -> None:
    served_at = client.post("/v1/predictions", json=valid_payload).json()["served_at"]

    assert served_at.endswith("Z")
    assert datetime.fromisoformat(served_at).utcoffset().total_seconds() == 0


def test_integer_values_are_valid_numbers(
    client: TestClient, valid_payload: dict
) -> None:
    valid_payload["features"]["alcohol"] = 12

    response = client.post("/v1/predictions", json=valid_payload)

    assert response.status_code == 200


def test_request_id_in_body_matches_header(
    client: TestClient, valid_payload: dict
) -> None:
    response = client.post("/v1/predictions", json=valid_payload)

    assert response.headers["X-Request-Id"] == response.json()["request_id"]
