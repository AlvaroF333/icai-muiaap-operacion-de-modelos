"""S10.4 — Rate limiting por cliente: 429 con `Retry-After`, sin esperas reales."""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from support import FRONT_KEY, OPS_KEY, FakeClock, build_settings, client_config

from wine_api.rate_limit import FixedWindowRateLimiter

# --- El limitador, sin HTTP ------------------------------------------------


def test_limiter_allows_up_to_the_limit_then_blocks(clock: FakeClock) -> None:
    limiter = FixedWindowRateLimiter(window_seconds=60, clock=clock)

    decisions = [limiter.hit("front", limit=3) for _ in range(4)]

    assert [d.allowed for d in decisions] == [True, True, True, False]
    assert [d.remaining for d in decisions] == [2, 1, 0, 0]
    assert decisions[-1].retry_after == 60


def test_retry_after_rounds_up_and_the_window_resets(clock: FakeClock) -> None:
    limiter = FixedWindowRateLimiter(window_seconds=60, clock=clock)
    limiter.hit("front", limit=1)

    clock.now += 59.2
    assert limiter.hit("front", limit=1).retry_after == 1

    clock.now += 0.8
    assert limiter.hit("front", limit=1).allowed is True


def test_each_client_has_its_own_window(clock: FakeClock) -> None:
    limiter = FixedWindowRateLimiter(window_seconds=60, clock=clock)
    limiter.hit("front", limit=1)

    assert limiter.hit("front", limit=1).allowed is False
    assert limiter.hit("ops", limit=1).allowed is True


# --- El limitador dentro de la API -----------------------------------------


@pytest.fixture
def limited_client(
    make_client: Callable[..., TestClient], clock: FakeClock
) -> TestClient:
    settings = build_settings(
        clients={
            "front": client_config(FRONT_KEY, ["predict"], rate_limit_per_minute=3),
            "ops": client_config(OPS_KEY, ["predict", "admin"]),
        }
    )
    return make_client(settings, rate_limiter=FixedWindowRateLimiter(clock=clock))


def test_allowed_responses_carry_rate_limit_headers(
    limited_client: TestClient, valid_payload: dict
) -> None:
    response = limited_client.post("/v1/predictions", json=valid_payload)

    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == "3"
    assert response.headers["X-RateLimit-Remaining"] == "2"


def test_exceeding_the_limit_returns_429_with_retry_after(
    limited_client: TestClient, valid_payload: dict, clock: FakeClock
) -> None:
    for _ in range(3):
        assert limited_client.post("/v1/predictions", json=valid_payload).is_success
    clock.now += 15.5

    response = limited_client.post("/v1/predictions", json=valid_payload)

    assert response.status_code == 429
    body = response.json()
    assert body["error"]["code"] == "rate_limited"
    assert response.headers["Retry-After"] == "45"
    assert response.headers["X-Request-Id"] == body["request_id"]
    # El límite es por cliente y la sonda de salud no lo consume.
    assert limited_client.get("/health").status_code == 200


def test_the_window_reopens_after_retry_after(
    limited_client: TestClient, valid_payload: dict, clock: FakeClock
) -> None:
    statuses = [
        limited_client.post("/v1/predictions", json=valid_payload).status_code
        for _ in range(4)
    ]
    assert statuses == [200, 200, 200, 429]

    clock.now += 60

    assert limited_client.post("/v1/predictions", json=valid_payload).status_code == 200


def test_admin_usage_reflects_requests_in_window(
    make_client: Callable[..., TestClient], valid_payload: dict, clock: FakeClock
) -> None:
    limiter = FixedWindowRateLimiter(clock=clock)
    front = make_client(rate_limiter=limiter)
    for _ in range(2):
        front.post("/v1/predictions", json=valid_payload)
    ops = make_client(api_key=OPS_KEY, rate_limiter=limiter)

    usage = {e["client"]: e for e in ops.get("/v1/admin/usage").json()["clients"]}

    assert usage["front"]["requests_in_window"] == 2
    assert usage["ops"]["requests_in_window"] == 0
