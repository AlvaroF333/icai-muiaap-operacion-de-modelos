"""Demo S10 · Bloque 4 — Secretos fuera del código y rate limiting de ventana fija.

Desde la raíz del módulo (la clave es de demo; elige la que quieras):

    DEMO_API_KEY=demo-limits-key uv run fastapi dev examples/limits_demo.py

Sin `DEMO_API_KEY` la aplicación no arranca: la configuración se valida al
iniciar, no en la primera petición. En PowerShell:
`$env:DEMO_API_KEY="demo-limits-key"; uv run fastapi dev examples/limits_demo.py`.

    # Siete peticiones seguidas con límite 5/min: 200 x5 y 429 x2
    for i in $(seq 1 7); do
      curl -s -o /dev/null -w "%{http_code} " -X POST http://127.0.0.1:8000/v1/scores \\
        -H "X-API-Key: demo-limits-key" -H "Content-Type: application/json" \\
        -d '{"age": 42, "income": 38000}'
    done; echo

    # La octava, con cabeceras: Retry-After dice cuántos segundos esperar
    curl -i -X POST http://127.0.0.1:8000/v1/scores -H "X-API-Key: demo-limits-key" \\
      -H "Content-Type: application/json" -d '{"age": 42, "income": 38000}'

    # La configuración efectiva, con la clave enmascarada por SecretStr
    curl -s http://127.0.0.1:8000/v1/config -H "X-API-Key: demo-limits-key"

El contador vive en memoria del proceso: `fastapi dev` lo reinicia al recargar y
con varios workers cada uno cuenta por su lado. En producción, Redis o el gateway.
"""

import math
import secrets
import time
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Annotated, Any

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# --- Configuración: tipada, validada y fuera del código ----------------------


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DEMO_", env_file=".env")

    api_key: SecretStr
    rate_limit_per_minute: int = Field(default=5, gt=0)
    cors_origins: list[str] = ["http://localhost:8501"]


# --- Rate limiting: ventana fija por clave ---------------------------------


class FixedWindowLimiter:
    def __init__(self, limit: int, window: float = 60.0, clock=time.monotonic):
        self.limit, self.window, self.clock = limit, window, clock
        self.windows: dict[str, tuple[float, int]] = {}

    def hit(self, key: str) -> float | None:
        """Devuelve `None` si la petición entra o los segundos que faltan si no."""

        now = self.clock()
        start, count = self.windows.get(key, (now, 0))
        if now - start >= self.window:
            start, count = now, 0
        if count >= self.limit:
            return self.window - (now - start)
        self.windows[key] = (start, count + 1)
        return None


# --- Aplicación ------------------------------------------------------------


def create_app(
    settings: Settings | None = None, clock: Callable[[], float] = time.monotonic
) -> FastAPI:
    """Los tests inyectan la configuración y un reloj falso."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        # Sin DEMO_API_KEY, `Settings()` lanza ValidationError aquí: fallo al arrancar.
        app.state.settings = settings or Settings()
        app.state.limiter = FixedWindowLimiter(
            app.state.settings.rate_limit_per_minute, clock=clock
        )
        yield

    app = FastAPI(title="Demo S10 · Configuración y límites", lifespan=lifespan)
    app.include_router(health)
    app.include_router(scores)
    app.include_router(config)
    return app


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


SettingsDep = Annotated[Settings, Depends(get_settings)]

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def check_api_key(
    settings: SettingsDep, api_key: Annotated[str | None, Security(api_key_header)]
) -> None:
    expected = settings.api_key.get_secret_value().encode()
    if not api_key or not secrets.compare_digest(api_key.encode(), expected):
        raise HTTPException(
            401, "Invalid API key", headers={"WWW-Authenticate": "ApiKey"}
        )


def enforce_rate_limit(request: Request) -> None:
    retry_after = request.app.state.limiter.hit("demo-client")
    if retry_after is not None:
        # Retry-After es un entero de segundos: redondea hacia arriba, nunca a 0.
        raise HTTPException(
            429,
            "Too many requests",
            headers={"Retry-After": str(math.ceil(retry_after))},
        )


# Primero se autentica y después se cuenta: un anónimo no gasta cuota ajena.
scores = APIRouter(
    prefix="/v1/scores",
    dependencies=[Depends(check_api_key), Depends(enforce_rate_limit)],
)
config = APIRouter(prefix="/v1/config", dependencies=[Depends(check_api_key)])
health = APIRouter()  # pública: sin clave y sin cuota


class ScoreRequest(BaseModel):
    age: int = Field(ge=18, le=100)
    income: float = Field(gt=0)


class ScoreResponse(BaseModel):
    score: float


@scores.post("")
def create_score(payload: ScoreRequest) -> ScoreResponse:
    return ScoreResponse(score=round(min(1.0, payload.income / 100_000), 2))


@health.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "ok"}


@config.get("")
def read_config(settings: SettingsDep) -> dict[str, Any]:
    """`SecretStr` se serializa como `**********`: la clave nunca sale."""

    return settings.model_dump(mode="json")


app = create_app()
