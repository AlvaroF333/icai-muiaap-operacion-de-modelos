"""Fixtures comunes a los tests de S9 (regresión) y de S10 (aceptación).

Los tests no leen `.env` ni el entorno del sistema: cada uno construye su
configuración con `build_settings` (ver `support.py`).
"""

import copy
import os
from collections.abc import Callable, Iterator
from contextlib import ExitStack

import pytest
from fastapi.testclient import TestClient
from support import FRONT_KEY, OPS_KEY, FakeClock, build_settings

from wine_api.main import create_app
from wine_api.predictor import DemoWinePredictor, Predictor
from wine_api.rate_limit import FixedWindowRateLimiter
from wine_api.schemas import VALID_FEATURES_EXAMPLE
from wine_api.settings import Settings


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ninguna variable `WINE_API_*` de tu terminal se cuela en los tests."""

    for name in list(os.environ):
        if name.startswith("WINE_API_"):
            monkeypatch.delenv(name)


@pytest.fixture
def valid_payload() -> dict:
    return {"features": copy.deepcopy(VALID_FEATURES_EXAMPLE)}


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


MakeClient = Callable[..., TestClient]


@pytest.fixture
def make_client() -> Iterator[MakeClient]:
    """Fábrica de clientes HTTP; cada uno con su app, su configuración y su clave."""

    with ExitStack() as stack:

        def _make(
            settings: Settings | None = None,
            *,
            api_key: str | None = FRONT_KEY,
            predictor: Predictor | None = None,
            rate_limiter: FixedWindowRateLimiter | None = None,
        ) -> TestClient:
            app = create_app(
                predictor=predictor or DemoWinePredictor(),
                settings=settings or build_settings(),
                rate_limiter=rate_limiter,
            )
            headers = {"X-API-Key": api_key} if api_key is not None else {}
            # raise_server_exceptions=False: queremos ver el 500 que recibe el cliente.
            test_client = TestClient(
                app, raise_server_exceptions=False, headers=headers
            )
            return stack.enter_context(test_client)

        yield _make


@pytest.fixture
def client(make_client: MakeClient) -> TestClient:
    """Cliente `front` (scope `predict`), como el front de Streamlit de S7."""

    return make_client()


@pytest.fixture
def ops_client(make_client: MakeClient) -> TestClient:
    """Cliente `ops` (scopes `predict` y `admin`)."""

    return make_client(api_key=OPS_KEY)


@pytest.fixture
def anonymous_client(make_client: MakeClient) -> TestClient:
    """Cliente sin cabecera `X-API-Key`."""

    return make_client(api_key=None)
