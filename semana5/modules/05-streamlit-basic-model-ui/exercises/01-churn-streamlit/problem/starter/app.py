"""Starter: conecta una función de inferencia pura con Streamlit."""

from collections.abc import Callable
from typing import Any

from churn_demo.model import ChurnPrediction, predict

Predictor = Callable[..., ChurnPrediction]


def collect_profile(st: Any) -> tuple[bool, dict[str, object]]:
    """Renderiza cuatro widgets dentro de un único formulario."""
    # Todo vive dentro del formulario: editar un widget no dispara inferencia,
    # solo el submit decide cuándo el rerun debe llamar al modelo.
    with st.form("churn_form"):
        values: dict[str, object] = {
            "tenure_months": st.slider(
                "Antigüedad (meses)", 0, 120, 12, key="tenure_months"
            ),
            "monthly_spend_eur": st.number_input(
                "Gasto mensual (€)",
                min_value=0.0,
                max_value=300.0,
                value=60.0,
                step=5.0,
                key="monthly_spend_eur",
            ),
            "support_calls": st.slider(
                "Llamadas a soporte (último trimestre)",
                0,
                20,
                1,
                key="support_calls",
            ),
            "has_annual_contract": st.checkbox(
                "Tiene contrato anual", value=False, key="has_annual_contract"
            ),
        }
        submitted = st.form_submit_button("Calcular riesgo")
    return bool(submitted), values


def render_prediction(st: Any, result: ChurnPrediction) -> None:
    """Muestra etiqueta, score orientativo y explicación."""
    # Solo se presenta lo que devuelve el contrato; la UI no recalcula nada.
    if result["will_churn"]:
        st.warning(result["label"])
    else:
        st.success(result["label"])
    st.metric("Score de riesgo (regla docente, umbral 0,50)", result["risk_score"])
    st.write(result["explanation"])


def run_app(st: Any, predictor: Predictor) -> None:
    """Conecta submit, llamada al predictor y actualización visible."""
    submitted, values = collect_profile(st)
    if not submitted:
        st.info("Ajusta el perfil y pulsa «Calcular riesgo» para obtener el score.")
        return

    try:
        result = predictor(**values)
    except ValueError:
        # Mensaje fijo: nunca se muestra str(error) ni el traceback al usuario.
        st.error(
            "No se pudo calcular el riesgo con estos valores. "
            "Revisa que estén dentro de los rangos del formulario y vuelve a enviar."
        )
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
