"""Configuración y secretos del servicio, leídos del entorno o de `.env`.

Todas las variables llevan el prefijo `WINE_API_`. Como ejemplo ya está migrada
`WINE_API_MODE`, que en S9 se leía con `os.environ`. Los tipos complejos
(`WINE_API_CLIENTS`, `WINE_API_CORS_ORIGINS`) se escribirán en JSON.
"""

from typing import Literal

from pydantic import (  # noqa: F401 - pistas para S10.1
    BaseModel,
    Field,
    SecretStr,
    field_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

Scope = Literal["predict", "admin"]


class ClientConfig(BaseModel):
    """Credencial, permisos y cuota de un cliente de la API."""

    # TODO S10.1a: declara los tres campos de un cliente:
    # - `key`: la API key. ¿Qué tipo de Pydantic evita que aparezca en un
    #   `repr`, en un `print` o en un log? Investiga `SecretStr` y cómo se lee
    #   su valor cuando de verdad lo necesitas.
    # - `scopes`: lista de `Scope`; un scope desconocido debe fallar al arrancar.
    # - `rate_limit_per_minute`: entero estrictamente positivo, 60 por defecto
    #   (`Field` con una restricción numérica).
    # Comprobación: tests/test_s10_1_settings.py (repr y configuración inválida).


class Settings(BaseSettings):
    """Configuración validada al arrancar: si algo es inválido, no arranca."""

    model_config = SettingsConfigDict(
        env_prefix="WINE_API_", env_file=".env", extra="ignore"
    )

    mode: Literal["ready", "unavailable"] = "ready"

    # TODO S10.1b: añade el resto de la configuración con valores por defecto
    # SEGUROS (la API debe arrancar sin `.env`, pero sin abrir nada):
    # - `clients`: diccionario nombre -> ClientConfig, vacío por defecto. Sin
    #   clientes no hay claves válidas: es la decisión «fail closed».
    # - `cors_origins`: lista de orígenes; por defecto solo el front de
    #   Streamlit (`http://localhost:8501`).
    # - `docs_enabled`: booleano, activado por defecto.
    # Además, rechaza `"*"` en `cors_origins` con un `field_validator`: la
    # configuración debe obligar a listar los orígenes.
    # ¿Por qué un error de configuración debe impedir arrancar en lugar de
    # aparecer en la primera petición?
    # Comprobación: uv run pytest -q tests/test_s10_1_settings.py
