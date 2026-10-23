"""S10.1 — Configuración y secretos fuera del código, validados al arrancar."""

import json
from pathlib import Path

import pytest
from pydantic import SecretStr, ValidationError
from support import FRONT_KEY, client_config

from wine_api.settings import Settings

ENV_EXAMPLE = Path(__file__).parents[1] / ".env.example"


def test_defaults_fail_closed_and_keep_cors_narrow() -> None:
    settings = Settings(_env_file=None)

    assert settings.mode == "ready"
    assert settings.clients == {}
    assert settings.cors_origins == ["http://localhost:8501"]
    assert settings.docs_enabled is True


def test_settings_are_read_from_prefixed_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clients = {"front": {"key": FRONT_KEY, "scopes": ["predict"]}}
    monkeypatch.setenv("WINE_API_MODE", "unavailable")
    monkeypatch.setenv("WINE_API_CLIENTS", json.dumps(clients))
    monkeypatch.setenv("WINE_API_CORS_ORIGINS", '["https://wine.example"]')
    monkeypatch.setenv("WINE_API_DOCS_ENABLED", "false")

    settings = Settings(_env_file=None)

    assert settings.mode == "unavailable"
    front = settings.clients["front"]
    assert isinstance(front.key, SecretStr)
    assert front.key.get_secret_value() == FRONT_KEY
    assert front.scopes == ["predict"]
    assert front.rate_limit_per_minute == 60
    assert settings.cors_origins == ["https://wine.example"]
    assert settings.docs_enabled is False


def test_api_keys_are_hidden_in_repr_and_dumps() -> None:
    settings = Settings(
        _env_file=None, clients={"front": client_config(FRONT_KEY, ["predict"])}
    )

    assert FRONT_KEY not in repr(settings)
    assert FRONT_KEY not in str(settings.clients)
    assert FRONT_KEY not in settings.model_dump_json()


@pytest.mark.parametrize(
    "overrides",
    [
        {"clients": {"x": client_config("k", ["root"])}},
        {"clients": {"x": client_config("k", ["predict"], rate_limit_per_minute=0)}},
        {"clients": {"x": {"scopes": ["predict"]}}},
        {"cors_origins": ["*"]},
    ],
    ids=["unknown-scope", "zero-rate-limit", "missing-key", "cors-wildcard"],
)
def test_invalid_configuration_is_rejected(overrides: dict) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **overrides)


def test_env_example_documents_every_setting_with_placeholders() -> None:
    settings = Settings(_env_file=ENV_EXAMPLE)

    assert set(settings.clients) == {"front", "ops"}
    assert settings.clients["front"].scopes == ["predict"]
    assert set(settings.clients["ops"].scopes) == {"predict", "admin"}
    for client in settings.clients.values():
        # Valores de ejemplo evidentes, nunca claves reales.
        assert client.key.get_secret_value().startswith("cambia-")
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    for variable in ("MODE", "CLIENTS", "CORS_ORIGINS", "DOCS_ENABLED"):
        assert f"WINE_API_{variable}=" in text
