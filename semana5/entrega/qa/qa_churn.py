"""QA 5.1 sin navegador: los cuatro casos de Churn con Streamlit real (AppTest).

Uso, desde la raíz del repositorio:

    uv run --project semana5/modules/05-streamlit-basic-model-ui/exercises/\
01-churn-streamlit/problem/starter python semana5/entrega/qa/qa_churn.py
"""

import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

STARTER = (
    Path(__file__).resolve().parents[2]
    / "modules/05-streamlit-basic-model-ui/exercises/01-churn-streamlit/problem/starter"
)
sys.path.insert(0, str(STARTER / "src"))

import churn_demo.model as churn_model  # noqa: E402

calls: list[dict[str, object]] = []
_original_predict = churn_model.predict


def counting_predict(**values: object) -> object:
    """Cuenta llamadas reales a predict() sin cambiar su resultado."""
    calls.append(values)
    return _original_predict(**values)


# app.py importa `predict` por nombre: se parchea antes de que AppTest lo cargue.
churn_model.predict = counting_predict


def show(at: AppTest) -> None:
    for kind in ("warning", "success", "info", "error", "metric", "markdown"):
        for element in getattr(at, kind):
            text = str(element.value)
            text = text if len(text) <= 110 else text[:110] + "…"
            print(f"   {kind}: {getattr(element, 'label', '')} {text}")


def set_profile(at: AppTest, tenure: int, spend: float, calls_: int) -> None:
    at.slider(key="tenure_months").set_value(tenure)
    at.number_input(key="monthly_spend_eur").set_value(spend)
    at.slider(key="support_calls").set_value(calls_)


app_path = str(STARTER / "app.py")

print("== Caso 1: arranque")
at = AppTest.from_file(app_path).run()
print(
    f"   widgets: {len(at.slider)} sliders, {len(at.number_input)} number_input, "
    f"{len(at.checkbox)} checkbox | llamadas: {len(calls)} | "
    f"excepciones: {len(at.exception)}"
)

print("== Caso 2: edición sin envío")
set_profile(at, 2, 95.0, 4)
at.run()
print(f"   llamadas: {len(calls)} | métricas visibles: {len(at.metric)}")

print("== Caso 3: submit válido (2, 95, 4, False)")
set_profile(at, 2, 95.0, 4)
at.button[0].click().run()
print(f"   llamadas: {len(calls)} | enviado: {calls[-1]}")
show(at)

print("== Caso 4: resultado actualizado (36, 35, 0, True)")
set_profile(at, 36, 35.0, 0)
at.checkbox(key="has_annual_contract").check()
at.button[0].click().run()
print(f"   llamadas: {len(calls)} | enviado: {calls[-1]}")
show(at)
