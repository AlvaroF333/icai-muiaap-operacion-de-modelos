"""Controlador de estados independiente de Streamlit."""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from time import perf_counter
from uuid import uuid4

from pydantic import BaseModel

from model_ui.contracts import PredictionPayload, UiState
from model_ui.gateway import InferenceGateway
from model_ui.presentation import build_prediction_view, to_user_facing_error
from model_ui.telemetry import Telemetry

logger = logging.getLogger(__name__)

StateEmitter = Callable[[UiState], None]
Clock = Callable[[], float]
RequestIdFactory = Callable[[], str]


class PredictionController:
    """Orquesta loading, gateway, errores y telemetría."""

    def __init__(
        self,
        gateway: InferenceGateway,
        *,
        telemetry: Telemetry | None = None,
        clock: Clock = perf_counter,
        request_id_factory: RequestIdFactory | None = None,
    ) -> None:
        self.gateway = gateway
        self.telemetry = telemetry or Telemetry()
        self._clock = clock
        self._request_id_factory = request_id_factory or (lambda: uuid4().hex[:10])

    def submit(
        self,
        values: Mapping[str, object],
        *,
        emit: StateEmitter | None = None,
    ) -> UiState:
        """Emite loading, mide, valida la salida y devuelve success/error.

        La latencia cubre la llamada al gateway y la validación de su salida.
        La telemetría recibe agregados (latencia, código, versiones), nunca
        `values`.
        """

        request_id = self._request_id_factory()
        if emit is not None:
            emit(UiState(phase="loading", request_id=request_id))

        started = self._clock()
        try:
            prediction = _validate_output(self.gateway.predict(values))
        except Exception as error:  # noqa: BLE001 - toda excepción acaba en la UI
            latency_ms = self._elapsed_ms(started)
            user_error = to_user_facing_error(error, request_id)
            # El log permite investigar por request_id sin volcar el payload.
            logger.warning(
                "request_id=%s code=%s exception=%s latency_ms=%.1f",
                request_id,
                user_error.code,
                type(error).__name__,
                latency_ms,
            )
            self.telemetry.record_error(user_error.code, latency_ms)
            state = UiState(phase="error", request_id=request_id, error=user_error)
        else:
            latency_ms = self._elapsed_ms(started)
            self.telemetry.record_success(
                latency_ms,
                model_version=prediction.model_version,
                preprocessing_version=prediction.preprocessing_version,
            )
            state = UiState(
                phase="success",
                request_id=request_id,
                view=build_prediction_view(prediction, latency_ms),
            )

        if emit is not None:
            emit(state)
        return state

    def _elapsed_ms(self, started: float) -> float:
        """Convierte segundos del reloj inyectado a milisegundos."""

        return round((self._clock() - started) * 1000, 3)


def _validate_output(raw: object) -> PredictionPayload:
    """Revalida la salida del gateway: en S7 llegará como JSON de un servicio."""

    if isinstance(raw, BaseModel):
        raw = raw.model_dump()
    return PredictionPayload.model_validate(raw)
