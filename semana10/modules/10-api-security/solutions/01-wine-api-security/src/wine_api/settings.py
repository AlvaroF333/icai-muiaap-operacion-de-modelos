"""Configuración y secretos del servicio, leídos del entorno o de `.env`.

Todas las variables llevan el prefijo `WINE_API_`. Los tipos complejos
(`WINE_API_CLIENTS`, `WINE_API_CORS_ORIGINS`) se escriben en JSON. Consulta
`.env.example`: documenta cada variable con valores de ejemplo, nunca reales.
"""

from typing import Literal

from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

Scope = Literal["predict", "admin"]


class ClientConfig(BaseModel):
    """Credencial, permisos y cuota de un cliente de la API."""

    key: SecretStr = Field(description="API key del cliente; oculta en `repr`.")
    scopes: list[Scope] = Field(description="Operaciones que la clave autoriza.")
    rate_limit_per_minute: int = Field(
        default=60, gt=0, description="Peticiones de predicción por minuto."
    )


class Settings(BaseSettings):
    """Configuración validada al arrancar: si algo es inválido, no arranca."""

    model_config = SettingsConfigDict(
        env_prefix="WINE_API_", env_file=".env", extra="ignore"
    )

    mode: Literal["ready", "unavailable"] = "ready"
    # Sin clientes no hay claves válidas: todo endpoint protegido responde 401.
    clients: dict[str, ClientConfig] = {}
    cors_origins: list[str] = ["http://localhost:8501"]
    docs_enabled: bool = True

    @field_validator("cors_origins")
    @classmethod
    def _reject_wildcard(cls, origins: list[str]) -> list[str]:
        if "*" in origins:
            raise ValueError("list the allowed origins explicitly; '*' is not allowed")
        return origins
