"""Vista UX: copy de salida y traducción de errores."""

from __future__ import annotations

from model_ui.contracts import (
    ErrorCode,
    PredictionPayload,
    PredictionView,
    UserFacingError,
)
from model_ui.errors import (
    ArtifactUnavailableError,
    InferenceTimeoutError,
    InputContractError,
)
from model_ui.policies import (
    DEFAULT_CONFIDENCE_POLICY,
    DEFAULT_LATENCY_POLICY,
    ConfidencePolicy,
    LatencyPolicy,
    classify_confidence,
    classify_latency,
)

QUALITY_LABELS = {
    "needs_review": "Requiere revisión",
    "acceptable": "Resultado aceptable",
    "excellent": "Resultado excelente",
}

CONFIDENCE_COPY = {
    "low": (
        "Confianza baja",
        "El resultado es orientativo y requiere revisión; "
        "la confianza no es una garantía.",
    ),
    "medium": (
        "Confianza intermedia",
        "Usa el resultado como señal orientativa y revisa su contexto antes de actuar.",
    ),
    "high": (
        "Confianza alta",
        "La confianza es alta para este modelo, pero no garantiza "
        "que la decisión sea correcta.",
    ),
}

LATENCY_COPY = {
    "within_target": (
        "Dentro del objetivo",
        "La respuesta quedó dentro del objetivo de la demo.",
    ),
    "above_target": (
        "Por encima del objetivo",
        "La respuesta llegó, pero la latencia supera el objetivo técnico de la demo.",
    ),
}


# Copy estable por código: nunca se interpola el texto de la excepción original,
# que puede contener rutas internas, valores de las features o secretos.
ERROR_COPY: dict[ErrorCode, tuple[str, str, str]] = {
    "invalid_input": (
        "Datos de entrada no válidos",
        "Algunos valores del formulario no cumplen el contrato de entrada del modelo.",
        "Revisa los valores del formulario y vuelve a enviarlo.",
    ),
    "artifact_unavailable": (
        "Modelo no disponible",
        "El modelo no está disponible ahora mismo; no se ha hecho ninguna predicción.",
        "Pulsa «Reintentar» más tarde; si persiste, comunica el request_id "
        "al equipo que opera la app.",
    ),
    "timeout": (
        "La inferencia tardó demasiado",
        "El modelo no respondió dentro del tiempo permitido.",
        "Pulsa «Reintentar»; si se repite, comunica el request_id.",
    ),
    "prediction_error": (
        "No se pudo obtener una predicción válida",
        "El modelo respondió, pero su salida no cumple el contrato y no se muestra.",
        "Pulsa «Reintentar»; si persiste, comunica el request_id.",
    ),
}


def build_prediction_view(
    prediction: PredictionPayload,
    latency_ms: float,
    *,
    confidence_policy: ConfidencePolicy = DEFAULT_CONFIDENCE_POLICY,
    latency_policy: LatencyPolicy = DEFAULT_LATENCY_POLICY,
) -> PredictionView:
    """Construye la vista con etiquetas, confianza, latencia y versiones."""

    confidence_level = classify_confidence(prediction.confidence, confidence_policy)
    latency_status = classify_latency(latency_ms, latency_policy)
    confidence_label, confidence_message = CONFIDENCE_COPY[confidence_level]
    latency_label, latency_message = LATENCY_COPY[latency_status]
    return PredictionView(
        quality_band=prediction.quality_band,
        quality_label=QUALITY_LABELS[prediction.quality_band],
        confidence=prediction.confidence,
        confidence_level=confidence_level,
        confidence_label=confidence_label,
        confidence_message=confidence_message,
        latency_ms=round(float(latency_ms), 1),
        latency_status=latency_status,
        latency_label=latency_label,
        latency_message=(
            f"{latency_message} Objetivo: {latency_policy.target_ms:.0f} ms."
        ),
        model_version=prediction.model_version,
        preprocessing_version=prediction.preprocessing_version,
    )


def to_user_facing_error(error: Exception, request_id: str) -> UserFacingError:
    """Asigna código estable, mensaje accionable y recuperación.

    El orden importa: `InputContractError` y `ValidationError` heredan de
    `ValueError`, así que solo la primera se trata como error de entrada.
    Cualquier excepción no prevista acaba en `prediction_error`.
    """

    code: ErrorCode
    if isinstance(error, InputContractError):
        code = "invalid_input"
    elif isinstance(error, (ArtifactUnavailableError, FileNotFoundError)):
        code = "artifact_unavailable"
    elif isinstance(error, (InferenceTimeoutError, TimeoutError)):
        code = "timeout"
    else:
        code = "prediction_error"
    title, message, recovery = ERROR_COPY[code]
    return UserFacingError(
        code=code,
        title=title,
        message=message,
        recovery=recovery,
        request_id=request_id,
    )
