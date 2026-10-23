from fastapi.testclient import TestClient


def test_health_reports_ready_model(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["model_status"] == "ready"
    assert body["model_version"] == "wine-quality-demo-v1"


def test_health_request_id_matches_header(client: TestClient) -> None:
    response = client.get("/health")

    assert response.headers["X-Request-Id"] == response.json()["request_id"]
    assert response.json()["request_id"].startswith("req_")
