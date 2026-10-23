"""Demo S10 · Bloques 1 y 2 — Autenticación con API key y autorización por scopes.

Desde la raíz del módulo:

    uv run fastapi dev examples/api_key_demo.py

Las dos claves de esta demo son públicas a propósito y solo sirven aquí. En la
práctica las claves se leen de la configuración (S10.1), nunca del código.

    # Sin clave: 401 con WWW-Authenticate
    curl -i -X POST http://127.0.0.1:8000/v1/scores \\
      -H "Content-Type: application/json" -d '{"age": 42, "income": 38000}'

    # Cliente front (scope predict): 200
    curl -i -X POST http://127.0.0.1:8000/v1/scores -H "X-API-Key: demo-front-key" \\
      -H "Content-Type: application/json" -d '{"age": 42, "income": 38000}'

    # front no tiene scope admin: 403; ops sí: 200
    curl -i http://127.0.0.1:8000/v1/admin/usage -H "X-API-Key: demo-front-key"
    curl -i http://127.0.0.1:8000/v1/admin/usage -H "X-API-Key: demo-ops-key"
"""

import secrets
from collections import Counter
from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

app = FastAPI(title="Demo S10 · API key y scopes", version="0.1.0")


@dataclass(frozen=True)
class Client:
    name: str
    key: str  # solo demo: en la práctica, SecretStr leído de la configuración
    scopes: frozenset[str]


# Claves de DEMO, públicas a propósito. Nunca pongas claves reales en el código.
CLIENTS = (
    Client(name="front", key="demo-front-key", scopes=frozenset({"predict"})),
    Client(name="ops", key="demo-ops-key", scopes=frozenset({"predict", "admin"})),
)

USAGE: Counter[str] = Counter()


# --- Bloque 1 · Autenticación: ¿quién llama? -------------------------------

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_client(api_key: Annotated[str | None, Security(api_key_header)]) -> Client:
    # compare_digest tarda lo mismo acierte o falle: no filtra la clave por tiempo.
    # Con `str` solo admite ASCII; la solución del workshop compara bytes.
    for client in CLIENTS:
        if api_key and secrets.compare_digest(api_key, client.key):
            return client
    raise HTTPException(
        status_code=401,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "ApiKey"},
    )


ClientDep = Annotated[Client, Depends(get_client)]


# --- Bloque 2 · Autorización: ¿qué puede hacer? ----------------------------


def require_scope(scope: str):
    def check_scope(client: ClientDep) -> Client:
        if scope not in client.scopes:
            raise HTTPException(status_code=403, detail=f"Missing scope: {scope}")
        return client

    return check_scope


scores = APIRouter(
    prefix="/v1/scores", dependencies=[Depends(require_scope("predict"))]
)
admin = APIRouter(prefix="/v1/admin", dependencies=[Depends(require_scope("admin"))])


class ScoreRequest(BaseModel):
    age: int = Field(ge=18, le=100)
    income: float = Field(gt=0)


class ScoreResponse(BaseModel):
    client: str
    score: float


class UsageResponse(BaseModel):
    requests: dict[str, int]


@scores.post("")
def create_score(payload: ScoreRequest, client: ClientDep) -> ScoreResponse:
    # `ClientDep` ya se resolvió en la dependencia del router: FastAPI la cachea
    # por petición, así que aquí no se vuelve a comparar la clave.
    USAGE[client.name] += 1
    return ScoreResponse(
        client=client.name, score=round(min(1.0, payload.income / 100_000), 2)
    )


@admin.get("/usage")
def read_usage() -> UsageResponse:
    return UsageResponse(requests=dict(USAGE))


@app.get("/health")
def read_health() -> dict[str, str]:
    """Pública: un balanceador o un orquestador la consulta sin credenciales."""

    return {"status": "ok"}


app.include_router(scores)
app.include_router(admin)
