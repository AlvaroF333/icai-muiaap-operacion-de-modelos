"""Demo S10 · Bloque 3 — CORS: qué orígenes de navegador pueden leer la API.

Desde la raíz del módulo:

    uv run fastapi dev examples/cors_demo.py

CORS lo aplica el NAVEGADOR, no el servidor: curl, Locust o un script pueden
llamar igualmente. CORS no autentica a nadie; solo decide qué páginas web
pueden leer las respuestas.

    # Preflight desde el front de Streamlit (origen permitido): 200
    curl -i -X OPTIONS http://127.0.0.1:8000/v1/scores \\
      -H "Origin: http://localhost:8501" \\
      -H "Access-Control-Request-Method: POST" \\
      -H "Access-Control-Request-Headers: content-type,x-api-key"

    # Preflight desde un origen desconocido: 400 y sin Access-Control-Allow-Origin
    curl -i -X OPTIONS http://127.0.0.1:8000/v1/scores \\
      -H "Origin: https://evil.example" \\
      -H "Access-Control-Request-Method: POST"
"""

import uuid

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Demo S10 · CORS", version="0.1.0")

# Lista explícita, nunca "*": en S10.5 sale de la configuración.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
    expose_headers=["X-Request-Id"],
)


class ScoreRequest(BaseModel):
    age: int = Field(ge=18, le=100)
    income: float = Field(gt=0)


class ScoreResponse(BaseModel):
    score: float


@app.post("/v1/scores")
def create_score(payload: ScoreRequest, response: Response) -> ScoreResponse:
    # Sin `expose_headers`, el JavaScript del front no podría leer esta cabecera.
    response.headers["X-Request-Id"] = f"req_{uuid.uuid4().hex[:12]}"
    return ScoreResponse(score=round(min(1.0, payload.income / 100_000), 2))


@app.get("/health")
def read_health() -> dict[str, str]:
    return {"status": "ok"}
