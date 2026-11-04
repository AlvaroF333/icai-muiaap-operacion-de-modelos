"""S6: app de S5 con estado explícito, gateway cacheado y UX operable."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from model_ui.contracts import UiState
from model_ui.controller import PredictionController
from model_ui.gateway import (
    FEATURE_NAMES,
    DemoGateway,
    InferenceGateway,
    PackagedBundleGateway,
    UnavailableGateway,
)
from model_ui.session import (
    LAST_STATE_KEY,
    LAST_VALUES_KEY,
    TELEMETRY_KEY,
    clear_last_state,
    initialize_session_state,
)

FEATURE_FIELDS = (
    ("fixed_acidity", "Fixed acidity", 0.0, 20.0, 7.4),
    ("volatile_acidity", "Volatile acidity", 0.0, 2.0, 0.7),
    ("citric_acid", "Citric acid", 0.0, 2.0, 0.0),
    ("residual_sugar", "Residual sugar", 0.0, 20.0, 1.9),
    ("chlorides", "Chlorides", 0.0, 1.0, 0.076),
    ("free_sulfur_dioxide", "Free sulfur dioxide", 0.0, 100.0, 11.0),
    ("total_sulfur_dioxide", "Total sulfur dioxide", 0.0, 300.0, 34.0),
    ("density", "Density", 0.98, 1.01, 0.9978),
    ("ph", "pH", 2.5, 4.5, 3.51),
    ("sulphates", "Sulphates", 0.0, 3.0, 0.56),
    ("alcohol", "Alcohol", 5.0, 20.0, 9.4),
)

assert tuple(field[0] for field in FEATURE_FIELDS) == FEATURE_NAMES


class InvalidOutputGateway:
    """Escenario docente: un backend que responde fuera del contrato de salida.

    Devuelve un dict, como hará un cliente HTTP en S7, para comprobar que el
    controlador revalida la salida y no la muestra si no cumple el contrato.
    """

    def predict(self, values: Mapping[str, object]) -> Any:
        """Ignora la muestra y devuelve una salida incompatible."""

        return {
            "quality_band": "unknown",
            "confidence": 1.7,
            "model_version": "demo-ui-v1",
            "preprocessing_version": "wine-red-features-v1",
        }


# Escenarios para la revisión visual sin `.joblib`. Solo se usan si no hay
# MODEL_UI_BUNDLE; no cambian el formulario ni el contrato de S4.
DEMO_SCENARIOS: dict[str, tuple[str, Callable[[], InferenceGateway]]] = {
    "ok": ("Respuesta normal", DemoGateway),
    "slow_low_confidence": (
        "Respuesta lenta con confianza baja",
        lambda: DemoGateway(
            quality_band="needs_review", confidence=0.42, delay_seconds=0.8
        ),
    ),
    "missing_bundle": ("Bundle ausente", UnavailableGateway),
    "invalid_output": ("Salida fuera de contrato", InvalidOutputGateway),
}
DEFAULT_SCENARIO = "ok"


def build_gateway(
    bundle_value: str | None, scenario: str = DEFAULT_SCENARIO
) -> InferenceGateway:
    """Selecciona el bundle configurado o conserva el gateway demo de S5."""

    if not bundle_value:
        _, factory = DEMO_SCENARIOS[scenario]
        return factory()
    try:
        return PackagedBundleGateway.from_bundle_path(Path(bundle_value))
    except Exception as error:  # noqa: BLE001 - se convierte en estado visible
        return UnavailableGateway(str(error))


def collect_values(st: Any) -> tuple[bool, dict[str, float]]:
    """Formulario heredado de S5; no es un TODO de esta semana."""

    values: dict[str, float] = {}
    with st.form("wine_quality_form"):
        st.caption("Formulario de S5: la inferencia se envía al pulsar el botón.")
        columns = st.columns(2)
        for index, (name, label, minimum, maximum, default) in enumerate(
            FEATURE_FIELDS
        ):
            with columns[index % 2]:
                values[name] = st.number_input(
                    label,
                    min_value=minimum,
                    max_value=maximum,
                    value=default,
                    key=f"input_{name}",
                )
        submitted = st.form_submit_button("Ejecutar inferencia")
    return submitted, values


def get_cached_gateway(
    st: Any, bundle_value: str | None, scenario: str = DEFAULT_SCENARIO
) -> InferenceGateway:
    """Carga el gateway una vez por (bundle, escenario) y lo reutiliza.

    Es un recurso compartido entre sesiones: solo contiene el bundle y su
    adaptador, nunca valores de una petición ni respuestas de una persona.
    """

    @st.cache_resource(show_spinner="Cargando el modelo…")
    def load_gateway(bundle_value: str | None, scenario: str) -> InferenceGateway:
        return build_gateway(bundle_value, scenario)

    return load_gateway(bundle_value, scenario)


def render_state(st: Any, state: UiState, target: Any | None = None) -> None:
    """Presenta idle/loading/success/error en un target de Streamlit.

    Con `target` (un `st.empty`) cada llamada reemplaza la anterior, así que
    loading → success/error ocupa siempre la misma zona de la pantalla.
    """

    area = target.container() if target is not None else st.container()

    if state.phase == "idle":
        area.info(
            "Introduce los valores de la muestra y pulsa «Ejecutar inferencia». "
            "El resultado aparecerá aquí."
        )
        return

    if state.phase == "loading":
        area.info("Procesando la muestra… el resultado aparecerá en esta zona.")
        return

    if state.phase == "error" and state.error is not None:
        error = state.error
        area.error(f"**{error.title}.** {error.message}")
        area.info(f"**Qué puedes hacer:** {error.recovery}")
        area.caption(f"Referencia de la petición: `{error.request_id}`")
        return

    view = state.view
    if view is None:
        area.warning("No hay un resultado que mostrar.")
        return

    quality_column, confidence_column, latency_column = area.columns(3)
    quality_column.metric("Categoría", view.quality_label)
    confidence_column.metric(
        "Confianza del modelo", f"{view.confidence:.0%}", help=view.confidence_label
    )
    latency_column.metric(
        "Latencia", f"{view.latency_ms:.0f} ms", help=view.latency_label
    )

    confidence_notice = area.warning if view.confidence_level == "low" else area.info
    confidence_notice(f"**{view.confidence_label}.** {view.confidence_message}")
    if view.latency_status == "above_target":
        area.warning(f"**{view.latency_label}.** {view.latency_message}")
    else:
        area.caption(view.latency_message)

    traceability = area.expander("Trazabilidad")
    traceability.markdown(
        f"- request_id: `{state.request_id}`\n"
        f"- model_version: `{view.model_version}`\n"
        f"- preprocessing_version: `{view.preprocessing_version}`"
    )


def run_prediction(
    st: Any,
    controller: PredictionController,
    values: Mapping[str, object],
    operation_area: Any,
    state_slot: Any,
) -> UiState:
    """Ejecuta una petición mostrando `st.status` y guarda el último estado."""

    with operation_area, st.status("Ejecutando inferencia…", expanded=False) as status:
        state = controller.submit(
            values,
            emit=lambda event: render_state(st, event, state_slot),
        )
        status.update(
            label=(
                "Inferencia completada"
                if state.phase == "success"
                else "La inferencia necesita atención"
            ),
            state="complete" if state.phase == "success" else "error",
        )
    st.session_state[LAST_STATE_KEY] = state
    return state


def select_scenario(st: Any, bundle_value: str | None) -> str:
    """Permite elegir el escenario docente cuando no hay bundle configurado."""

    if bundle_value:
        st.sidebar.caption("Usando el bundle de S4 configurado en MODEL_UI_BUNDLE.")
        return DEFAULT_SCENARIO
    return st.sidebar.selectbox(
        "Escenario de demostración",
        options=list(DEMO_SCENARIOS),
        format_func=lambda key: DEMO_SCENARIOS[key][0],
        help="Solo docencia: cambia el gateway para observar éxito, lentitud y "
        "errores sin tocar el formulario de S5.",
    )


def main() -> None:
    """Ejecuta la app de S5 con estado avanzado de S6."""

    try:
        import streamlit as st
    except ModuleNotFoundError as error:
        raise SystemExit(
            "Instala Streamlit con `uv run --with streamlit streamlit run app.py`."
        ) from error

    st.set_page_config(page_title="Wine Quality · S6", page_icon="🍷")
    st.title("Inferencia de calidad de vino")
    st.caption("S6: la app de S5 ahora conserva estado y comunica la operación.")

    initialize_session_state(st.session_state)
    bundle_value = os.getenv("MODEL_UI_BUNDLE")
    scenario = select_scenario(st, bundle_value)
    gateway = get_cached_gateway(st, bundle_value, scenario)
    telemetry = st.session_state[TELEMETRY_KEY]
    controller = PredictionController(gateway, telemetry=telemetry)

    submitted, values = collect_values(st)
    operation_area = st.container()
    state_slot = st.empty()
    if submitted:
        st.session_state[LAST_VALUES_KEY] = values
        run_prediction(st, controller, values, operation_area, state_slot)

    # El resultado sale de session_state: sobrevive a cualquier rerun.
    state = st.session_state[LAST_STATE_KEY]
    render_state(st, state, state_slot)

    # Reintentar con los mismos valores no arregla una entrada inválida.
    can_retry = (
        state.phase == "error"
        and state.error is not None
        and state.error.code != "invalid_input"
        and bool(st.session_state[LAST_VALUES_KEY])
    )
    retry_column, clear_column = st.columns(2)
    if retry_column.button(
        "Reintentar",
        disabled=not can_retry,
        help="Reenvía el último envío sin volver a rellenar el formulario.",
    ):
        if state.error is not None and state.error.code == "artifact_unavailable":
            # No se deja cacheado para siempre un gateway que falló al cargar.
            st.cache_resource.clear()
            gateway = get_cached_gateway(st, bundle_value, scenario)
            controller = PredictionController(gateway, telemetry=telemetry)
        run_prediction(
            st,
            controller,
            st.session_state[LAST_VALUES_KEY],
            operation_area,
            state_slot,
        )
        st.rerun()
    clear_column.button(
        "Limpiar último resultado",
        on_click=clear_last_state,
        args=(st.session_state,),
        disabled=state.phase == "idle",
        help="Vuelve al estado inicial; la telemetría de la sesión se conserva.",
    )

    st.divider()
    st.subheader("Telemetría de la sesión")
    st.json(telemetry.snapshot().__dict__)
    st.caption("Solo se muestran agregados; no se guardan las features en Telemetry.")


if __name__ == "__main__":
    main()
