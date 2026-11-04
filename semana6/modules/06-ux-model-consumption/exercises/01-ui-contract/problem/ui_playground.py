"""Laboratorio visual de S6: componentes Streamlit sin reimplementar inferencia."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import streamlit as st

UiPhase = Literal["idle", "loading", "success", "error"]


@dataclass(frozen=True)
class Preview:
    phase: UiPhase
    quality_label: str | None = None
    confidence: float | None = None
    latency_ms: float | None = None
    request_id: str = "s6-demo-42af"


PREVIEWS = {
    "Sin petición": Preview("idle"),
    "Ejecutando": Preview("loading"),
    "Éxito — confianza intermedia": Preview(
        "success",
        quality_label="Resultado aceptable",
        confidence=0.74,
        latency_ms=118.0,
    ),
    "Éxito — confianza baja y lento": Preview(
        "success",
        quality_label="Requiere revisión",
        confidence=0.51,
        latency_ms=412.0,
    ),
    "Error recuperable": Preview("error"),
}


def render_preview(preview: Preview) -> None:
    """Dibuja una propuesta de UI; la pareja decide qué ajustar y por qué."""

    if preview.phase == "idle":
        st.info("Completa el formulario y pulsa «Ejecutar inferencia».")
        return

    if preview.phase == "loading":
        with st.status("Validando la muestra y ejecutando el modelo…", expanded=False):
            st.write("La pantalla reserva esta zona; el formulario no desaparece.")
        return

    if preview.phase == "error":
        st.error("Revisa los datos")
        st.write("La muestra no cumple el contrato de entrada.")
        st.info("Corrige los campos indicados y vuelve a enviar la petición.")
        st.caption(f"Request ID: {preview.request_id}")
        return

    assert preview.quality_label is not None
    assert preview.confidence is not None
    assert preview.latency_ms is not None

    # Cambio de la pareja: sin banner `st.success`. Duplicaba la categoría y
    # pintaba de verde también «Requiere revisión», sugiriendo que el modelo
    # «acierta». El éxito es de la operación; la categoría va en una métrica.
    category, confidence, latency = st.columns(3)
    category.metric("Categoría", preview.quality_label)
    confidence.metric("Confianza", f"{preview.confidence:.0%}")
    latency.metric("Latencia", f"{preview.latency_ms:.0f} ms")

    if preview.confidence < 0.60:
        st.warning(
            "Confianza baja: el resultado es orientativo y requiere revisión; "
            "no es una garantía."
        )
    else:
        st.info("Usa la predicción como una señal y revísala en su contexto.")

    if preview.latency_ms > 300:
        st.warning("La respuesta llegó, pero supera el objetivo técnico de la demo.")
    else:
        st.caption("La respuesta quedó dentro del objetivo de latencia de la demo.")

    with st.expander("Trazabilidad"):
        st.json(
            {
                "model_version": "wine-quality-rf-demo-v1",
                "preprocessing_version": "wine-red-features-v1",
                "request_id": preview.request_id,
            }
        )


def main() -> None:
    st.set_page_config(page_title="Laboratorio UI · S6", page_icon="🍷", layout="wide")
    st.title("Laboratorio visual · Inferencia de calidad de vino")
    st.caption(
        "No se ejecuta un modelo: la pantalla permite discutir y probar la UX "
        "antes de implementar el estado avanzado en el taller."
    )

    with st.sidebar:
        st.header("Actividad")
        st.write("Elegid un escenario y justificad cada componente visible.")
        st.divider()
        st.markdown(
            "**No cambiar:** contrato de S4, 11 features, gateway e inferencia."
        )
        st.markdown(
            "**Sí cambiar:** jerarquía, mensajes, estados y detalle técnico."
        )

    with st.container(border=True):
        st.subheader("Formulario heredado de S5")
        st.caption("En Clase 2 se reutilizará este formulario; aquí no se rediseña.")
        with st.form("s5_form_preview"):
            left, right = st.columns(2)
            left.number_input(
                "Fixed acidity", min_value=0.0, max_value=20.0, value=7.4
            )
            right.number_input(
                "Volatile acidity", min_value=0.0, max_value=2.0, value=0.7
            )
            st.form_submit_button("Ejecutar inferencia", disabled=True)

    scenario = st.selectbox("Escenario a previsualizar", list(PREVIEWS))
    st.divider()
    state_slot = st.empty()
    with state_slot.container(border=True):
        render_preview(PREVIEWS[scenario])

    st.divider()
    st.subheader("Checklist de revisión entre parejas")
    st.checkbox("El estado de operación es visible", key="check_status")
    st.checkbox("Categoría, confianza y latencia tienen jerarquía", key="check_metrics")
    st.checkbox("El detalle técnico no invade el resultado", key="check_traceability")
    st.checkbox("El copy no promete certeza ni muestra detalles internos", key="check_copy")


if __name__ == "__main__":
    main()
