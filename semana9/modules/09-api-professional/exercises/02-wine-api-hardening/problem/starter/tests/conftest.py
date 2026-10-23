import copy
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from wine_api.main import create_app
from wine_api.predictor import DemoWinePredictor
from wine_api.schemas import VALID_FEATURES_EXAMPLE


@pytest.fixture
def valid_payload() -> dict:
    return {"features": copy.deepcopy(VALID_FEATURES_EXAMPLE)}


@pytest.fixture
def client() -> Iterator[TestClient]:
    # raise_server_exceptions=False: queremos ver el 500 que recibe el cliente.
    app = create_app(predictor=DemoWinePredictor())
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
