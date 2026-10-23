"""Constantes y constructores compartidos por los tests.

Las claves de este archivo son de test: no valen fuera de la suite.
"""

from typing import Any

from wine_api.settings import Settings

FRONT_KEY = "test-front-key-not-for-production"
OPS_KEY = "test-ops-key-not-for-production"


class FakeClock:
    """Reloj controlado por el test: avanza con `clock.now += segundos`."""

    def __init__(self) -> None:
        self.now = 1_000.0

    def __call__(self) -> float:
        return self.now


def client_config(
    key: str, scopes: list[str], rate_limit_per_minute: int = 1_000
) -> dict[str, Any]:
    return {
        "key": key,
        "scopes": scopes,
        "rate_limit_per_minute": rate_limit_per_minute,
    }


def build_settings(**overrides: Any) -> Settings:
    """Configuración de test con dos clientes; `overrides` sustituye campos."""

    values: dict[str, Any] = {
        "mode": "ready",
        "clients": {
            "front": client_config(FRONT_KEY, ["predict"]),
            "ops": client_config(OPS_KEY, ["predict", "admin"]),
        },
        "cors_origins": ["http://localhost:8501"],
        "docs_enabled": True,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)
