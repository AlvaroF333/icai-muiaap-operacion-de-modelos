"""Punto de entrada de la API: `fastapi dev` usa `wine_api.main:app`."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from wine_api.errors import install_error_handlers
from wine_api.predictor import Predictor, build_predictor
from wine_api.rate_limit import FixedWindowRateLimiter
from wine_api.request_id import REQUEST_ID_HEADER, request_id_middleware
from wine_api.routers import admin, health, predictions
from wine_api.security import API_KEY_HEADER
from wine_api.settings import Settings

# 2.0.0: exigir `X-API-Key` rompe a los clientes anónimos de 1.x (cambio mayor).
API_VERSION = "2.0.0"

API_DESCRIPTION = """
Servicio de inferencia del proyecto **Wine Quality** de Operación de Modelos.

- `POST /v1/predictions` y `/v1/admin/*` exigen la cabecera `X-API-Key`; pulsa
  **Authorize** para probarlos desde aquí. `GET /health` es público.
- Cada clave tiene scopes (`predict`, `admin`) y una cuota por minuto: un `429`
  trae `Retry-After` con los segundos que hay que esperar.
- Todas las respuestas incluyen `request_id` y la cabecera `X-Request-Id`.
- Todos los errores comparten el sobre `ErrorResponse`; programa contra
  `error.code`, no contra `error.message`.
- La predicción es determinista y docente: no es una garantía de calidad.
"""

OPENAPI_TAGS = [
    {"name": "health", "description": "Disponibilidad del servicio y del modelo."},
    {"name": "predictions", "description": "Inferencia de calidad de vino tinto."},
    {"name": "admin", "description": "Operación del servicio; exige scope `admin`."},
]


def create_app(
    predictor: Predictor | None = None,
    settings: Settings | None = None,
    rate_limiter: FixedWindowRateLimiter | None = None,
) -> FastAPI:
    """Crea la aplicación; los tests inyectan predictor, configuración y reloj."""

    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        app.state.predictor = predictor or build_predictor(settings.mode)
        yield

    docs_enabled = settings.docs_enabled
    app = FastAPI(
        title="Wine Quality API",
        version=API_VERSION,
        summary="Predicción de la banda de calidad de vinos tintos.",
        description=API_DESCRIPTION,
        openapi_tags=OPENAPI_TAGS,
        lifespan=lifespan,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
    )
    app.state.settings = settings
    app.state.rate_limiter = rate_limiter or FixedWindowRateLimiter()

    app.middleware("http")(request_id_middleware)
    # El último middleware añadido es el más externo: CORS responde al preflight
    # antes de que la petición llegue a la autenticación.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", API_KEY_HEADER],
        expose_headers=[REQUEST_ID_HEADER, "Retry-After", "X-RateLimit-Remaining"],
        allow_credentials=False,
    )
    install_error_handlers(app)
    app.include_router(health.router)
    app.include_router(predictions.router)
    app.include_router(admin.router)
    return app


app = create_app()
