"""Demo S10 · Bloque 2 — Validar un Bearer JWT firmado con HS256 (PyJWT).

Desde la raíz del módulo:

    uv run fastapi dev examples/jwt_demo.py

`POST /token` existe SOLO para la demo: hace de proveedor de identidad (IdP) y
firma tokens sin pedir contraseña. En un sistema real el token lo emite el IdP
(Entra ID, Auth0, Keycloak...) tras autenticar a la persona; la API solo valida.

    # Emitir un token válido (15 min) y usarlo
    TOKEN=$(curl -s -X POST http://127.0.0.1:8000/token \\
      -H "Content-Type: application/json" -d '{"sub": "ana"}' | jq -r .access_token)
    curl -i http://127.0.0.1:8000/v1/me -H "Authorization: Bearer $TOKEN"

    # Fabricar tokens defectuosos (solo demo): caducado u otra audiencia -> 401
    curl -s -X POST http://127.0.0.1:8000/token -H "Content-Type: application/json" \\
      -d '{"sub": "ana", "expires_in": -60}'
    curl -s -X POST http://127.0.0.1:8000/token -H "Content-Type: application/json" \\
      -d '{"sub": "ana", "audience": "otra-api"}'

Pega el token en <https://jwt.io> para ver que el payload NO está cifrado: solo
firmado. Nunca metas datos sensibles en los claims.
"""

import os
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Literal

import jwt
from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

# Secreto de DEMO. En la práctica se lee de un gestor de secretos o de `.env`.
SECRET_KEY = os.environ.get(
    "DEMO_JWT_SECRET", "solo-demo-no-usar-en-produccion-0123456789"
)
TOKEN_LIFETIME = timedelta(minutes=15)

app = FastAPI(title="Demo S10 · JWT", version="0.1.0")


class TokenRequest(BaseModel):
    """Petición al IdP simulado; los dos últimos campos existen solo para la demo."""

    sub: str = Field(min_length=1, max_length=64, examples=["ana"])
    scope: Literal["predict", "admin"] = "predict"
    expires_in: int = Field(
        default=int(TOKEN_LIFETIME.total_seconds()),
        ge=-60,
        le=900,
        description="Segundos de vida. Negativo fabrica un token caducado (demo).",
    )
    audience: str = Field(
        default="wine-api", description="Cámbialo para ver un 401 por audiencia."
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class MeResponse(BaseModel):
    sub: str
    scope: str
    expires_at: datetime


def issue_token(
    sub: str,
    scope: str = "predict",
    *,
    expires_in: int = int(TOKEN_LIFETIME.total_seconds()),
    audience: str = "wine-api",
) -> str:
    """Firma un token como lo haría el IdP: `iss`, `aud` y `exp` son obligatorios."""

    now = datetime.now(UTC)
    claims = {
        "sub": sub,
        "scope": scope,
        "iss": "muiaap-demo-idp",
        "aud": audience,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }
    return jwt.encode(claims, SECRET_KEY, algorithm="HS256")


bearer = HTTPBearer(auto_error=False)


def get_claims(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Security(bearer)],
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(
            401, "Missing token", headers={"WWW-Authenticate": "Bearer"}
        )
    try:
        # `algorithms` es una lista blanca: nunca aceptes el `alg` que dice el token.
        return jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=["HS256"],
            audience="wine-api",
            issuer="muiaap-demo-idp",
        )
    except jwt.InvalidTokenError as exc:
        # Caducado, otra audiencia, firma alterada...: al cliente, siempre lo mismo.
        raise HTTPException(
            401, "Invalid token", headers={"WWW-Authenticate": "Bearer"}
        ) from exc


ClaimsDep = Annotated[dict[str, Any], Depends(get_claims)]


@app.post("/token")
def create_token(payload: TokenRequest) -> TokenResponse:
    """SOLO DEMO: simula el IdP. Una API de inferencia no emite sus propios tokens."""

    token = issue_token(
        payload.sub,
        payload.scope,
        expires_in=payload.expires_in,
        audience=payload.audience,
    )
    return TokenResponse(access_token=token, expires_in=payload.expires_in)


@app.get("/v1/me")
def read_me(claims: ClaimsDep) -> MeResponse:
    return MeResponse(
        sub=claims["sub"],
        scope=claims["scope"],
        expires_at=datetime.fromtimestamp(claims["exp"], UTC),
    )
