"""Tests de las demos de S10.

Son la comprobación de las demos y, a la vez, el ejemplo de cómo se prueba la
seguridad sin servidor: `uv run pytest -q` desde la raíz del módulo.
"""

from collections.abc import Iterator

import api_key_demo
import cors_demo
import jwt
import jwt_demo
import limits_demo
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

SCORE = {"age": 42, "income": 38000}


class FakeClock:
    """Reloj controlado por el test: nada de `time.sleep`."""

    def __init__(self) -> None:
        self.now = 1_000.0

    def __call__(self) -> float:
        return self.now


# --- Bloques 1 y 2 · API key y scopes -------------------------------------


@pytest.fixture
def api_client() -> TestClient:
    api_key_demo.USAGE.clear()
    return TestClient(api_key_demo.app)


def test_missing_api_key_returns_401_with_challenge(api_client: TestClient) -> None:
    response = api_client.post("/v1/scores", json=SCORE)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "ApiKey"


def test_wrong_api_key_returns_401(api_client: TestClient) -> None:
    response = api_client.post(
        "/v1/scores", json=SCORE, headers={"X-API-Key": "demo-front-kez"}
    )

    assert response.status_code == 401


def test_front_can_score_but_cannot_read_usage(api_client: TestClient) -> None:
    headers = {"X-API-Key": "demo-front-key"}

    scored = api_client.post("/v1/scores", json=SCORE, headers=headers)
    usage = api_client.get("/v1/admin/usage", headers=headers)

    assert scored.status_code == 200
    assert scored.json()["client"] == "front"
    assert usage.status_code == 403
    assert usage.json()["detail"] == "Missing scope: admin"


def test_ops_can_read_usage(api_client: TestClient) -> None:
    api_client.post("/v1/scores", json=SCORE, headers={"X-API-Key": "demo-front-key"})

    response = api_client.get("/v1/admin/usage", headers={"X-API-Key": "demo-ops-key"})

    assert response.status_code == 200
    assert response.json() == {"requests": {"front": 1}}


def test_health_is_public(api_client: TestClient) -> None:
    assert api_client.get("/health").status_code == 200


def test_openapi_declares_the_api_key_scheme(api_client: TestClient) -> None:
    schema = api_client.get("/openapi.json").json()

    scheme = schema["components"]["securitySchemes"]["APIKeyHeader"]
    assert scheme == {"type": "apiKey", "in": "header", "name": "X-API-Key"}
    assert schema["paths"]["/v1/scores"]["post"]["security"] == [{"APIKeyHeader": []}]
    assert "security" not in schema["paths"]["/health"]["get"]


# --- Bloque 2 · JWT --------------------------------------------------------


@pytest.fixture
def jwt_client() -> TestClient:
    return TestClient(jwt_demo.app)


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_valid_token_returns_its_claims(jwt_client: TestClient) -> None:
    token = jwt_client.post("/token", json={"sub": "ana"}).json()["access_token"]

    response = jwt_client.get("/v1/me", headers=bearer(token))

    assert response.status_code == 200
    assert response.json()["sub"] == "ana"
    assert response.json()["scope"] == "predict"


def test_missing_token_returns_401_with_bearer_challenge(
    jwt_client: TestClient,
) -> None:
    response = jwt_client.get("/v1/me")

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "token",
    [
        jwt_demo.issue_token("ana", expires_in=-60),
        jwt_demo.issue_token("ana", audience="otra-api"),
        jwt.encode(
            {"sub": "ana", "aud": "wine-api", "iss": "muiaap-demo-idp", "exp": 4e9},
            "otra-clave-que-no-es-la-del-servidor-0123",
            algorithm="HS256",
        ),
    ],
    ids=["expired", "wrong-audience", "wrong-signature"],
)
def test_invalid_tokens_return_401(jwt_client: TestClient, token: str) -> None:
    response = jwt_client.get("/v1/me", headers=bearer(token))

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


# --- Bloque 3 · CORS -------------------------------------------------------


def preflight(origin: str) -> dict[str, str]:
    return {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type,x-api-key",
    }


def test_preflight_from_allowed_origin_is_accepted() -> None:
    client = TestClient(cors_demo.app)

    response = client.options("/v1/scores", headers=preflight("http://localhost:8501"))

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:8501"
    assert "x-api-key" in response.headers["access-control-allow-headers"].lower()


def test_preflight_from_unknown_origin_is_rejected() -> None:
    client = TestClient(cors_demo.app)

    response = client.options("/v1/scores", headers=preflight("https://evil.example"))

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_allowed_origin_can_read_the_request_id() -> None:
    client = TestClient(cors_demo.app)

    response = client.post(
        "/v1/scores", json=SCORE, headers={"Origin": "http://localhost:8501"}
    )

    assert response.headers["access-control-allow-origin"] == "http://localhost:8501"
    assert response.headers["access-control-expose-headers"] == "X-Request-Id"


# --- Bloque 4 · Configuración y rate limiting ------------------------------


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def limits_client(clock: FakeClock) -> Iterator[TestClient]:
    settings = limits_demo.Settings(
        _env_file=None, api_key="test-key", rate_limit_per_minute=2
    )
    app = limits_demo.create_app(settings=settings, clock=clock)
    with TestClient(app) as client:
        client.headers["X-API-Key"] = "test-key"
        yield client


def test_settings_are_read_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DEMO_API_KEY", "from-env")
    monkeypatch.setenv("DEMO_RATE_LIMIT_PER_MINUTE", "10")
    monkeypatch.setenv("DEMO_CORS_ORIGINS", '["https://wine.example"]')

    settings = limits_demo.Settings(_env_file=None)

    assert settings.api_key.get_secret_value() == "from-env"
    assert settings.rate_limit_per_minute == 10
    assert settings.cors_origins == ["https://wine.example"]
    assert "from-env" not in repr(settings)


def test_missing_api_key_fails_at_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DEMO_API_KEY", raising=False)

    with pytest.raises(ValidationError):
        limits_demo.Settings(_env_file=None)


def test_config_endpoint_masks_the_secret(limits_client: TestClient) -> None:
    body = limits_client.get("/v1/config").json()

    assert body["api_key"] == "**********"
    assert body["rate_limit_per_minute"] == 2


def test_rate_limit_returns_429_with_retry_after(
    limits_client: TestClient, clock: FakeClock
) -> None:
    statuses = [limits_client.post("/v1/scores", json=SCORE).status_code for _ in "abc"]
    assert statuses == [200, 200, 429]

    clock.now += 30.2
    blocked = limits_client.post("/v1/scores", json=SCORE)
    assert blocked.status_code == 429
    assert blocked.headers["Retry-After"] == "30"

    assert limits_client.get("/health", headers={"X-API-Key": ""}).status_code == 200

    clock.now += 29.8
    assert limits_client.post("/v1/scores", json=SCORE).status_code == 200


def test_anonymous_requests_do_not_consume_quota(limits_client: TestClient) -> None:
    anonymous = {"X-API-Key": ""}
    for _ in range(5):
        response = limits_client.post("/v1/scores", json=SCORE, headers=anonymous)
        assert response.status_code == 401

    assert limits_client.post("/v1/scores", json=SCORE).status_code == 200
