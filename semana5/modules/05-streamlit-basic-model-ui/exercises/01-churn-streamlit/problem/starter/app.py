"""Starter: conecta una función de inferencia pura con Streamlit."""

from collections.abc import Callable
from typing import Any

from churn_demo.model import ChurnPrediction, predict

Predictor = Callable[..., ChurnPrediction]


def collect_profile(st: Any) -> tuple[bool, dict[str, object]]:
    """Renderiza cuatro widgets dentro de un único formulario."""
    with st.form("churn_form"):
        tenure = st.slider("Antigüedad (meses)", 0, 120, 12, key="tenure_months")
        spend = st.number_input(
            "Gasto mensual (EUR)",
            min_value=0.0,
            max_value=300.0,
            value=60.0,
            step=1.0,
            key="monthly_spend_eur",
        )
        calls = st.slider("Llamadas a soporte", 0, 20, 1, key="support_calls")
        annual = st.checkbox("Contrato anual", value=False, key="has_annual_contract")
        submitted = st.form_submit_button("Calcular riesgo")

    values: dict[str, object] = {
        "tenure_months": tenure,
        "monthly_spend_eur": spend,
        "support_calls": calls,
        "has_annual_contract": annual,
    }
    return submitted, values


def render_prediction(st: Any, result: ChurnPrediction) -> None:
    """Muestra etiqueta, score orientativo y explicación."""
    if result["will_churn"]:
        st.warning(result["label"])
    else:
        st.success(result["label"])
    st.metric("Score orientativo (0 a 1)", f"{result['risk_score']:.2f}")
    st.write(result["explanation"])


def run_app(st: Any, predictor: Predictor) -> None:
    """Conecta submit, llamada al predictor y actualización visible."""
    submitted, values = collect_profile(st)
    if not submitted:
        st.info("Completa el formulario y pulsa Calcular riesgo.")
        return

    try:
        result = predictor(**values)
    except ValueError:
        st.error("No se pudo calcular el riesgo. Revisa los datos e inténtalo de nuevo.")
        return
    render_prediction(st, result)


def main() -> None:
    """Configura la página real y delega el flujo comprobable en run_app."""
    import streamlit as st

    st.set_page_config(page_title="Churn sintético · S5", page_icon="📉")
    st.title("¿Qué cliente podría darse de baja?")
    st.caption("Caso docente sintético; el score no es una probabilidad calibrada.")
    run_app(st, predict)


if __name__ == "__main__":
    main()
