"""QA 5.2 sin navegador: los cuatro casos de Wine con el bundle real (AppTest).

Uso, desde la raíz del repositorio (PowerShell):

    $env:MODEL_UI_BUNDLE = "$PWD\\semana5\\models\\wine_quality_bundle"
    uv run --project semana5/modules/05-streamlit-basic-model-ui/exercises/\
02-first-streamlit/problem/starter --with 'streamlit>=1.40,<2.0' \
python semana5/entrega/qa/qa_wine.py
"""

import os
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

STARTER = (
    Path(__file__).resolve().parents[2]
    / "modules/05-streamlit-basic-model-ui/exercises/02-first-streamlit/problem/starter"
)
sys.path.insert(0, str(STARTER / "src"))

from model_ui import gateway as wine_gateway  # noqa: E402

calls: list[dict[str, object]] = []
_original_predict = wine_gateway.PackagedBundleGateway.predict


def counting_predict(self: object, values: dict[str, object]) -> object:
    """Cuenta llamadas reales a gateway.predict(values) sin cambiar su resultado."""
    calls.append(dict(values))
    return _original_predict(self, values)


wine_gateway.PackagedBundleGateway.predict = counting_predict


def visible_texts(at: AppTest) -> list[str]:
    texts = []
    for kind in ("success", "error", "info", "caption", "markdown", "metric"):
        for element in getattr(at, kind):
            texts.append(f"{kind}: {getattr(element, 'label', '')} {element.value}")
    return texts


app_path = str(STARTER / "app.py")
bundle = os.environ["MODEL_UI_BUNDLE"]

print("== Caso 1: arranque con bundle real")
at = AppTest.from_file(app_path, default_timeout=60).run()
print(
    f"   number_inputs: {len(at.number_input)} | llamadas: {len(calls)} | "
    f"excepciones: {len(at.exception)}"
)

print("== Caso 2: edición sin envío")
at.number_input(key="input_alcohol").set_value(12.5)
at.number_input(key="input_volatile_acidity").set_value(0.3)
at.run()
print(f"   llamadas: {len(calls)} | métricas visibles: {len(at.metric)}")

print("== Caso 3: submit válido")
at.number_input(key="input_alcohol").set_value(12.5)
at.button[0].click().run()
print(f"   llamadas: {len(calls)} | alcohol enviado: {calls[-1]['alcohol']}")
for text in visible_texts(at):
    print("   ", text)

print("== Caso 4: bundle ausente / inválido")
for value in (None, str(Path(bundle) / "no-existe")):
    if value is None:
        os.environ.pop("MODEL_UI_BUNDLE", None)
    else:
        os.environ["MODEL_UI_BUNDLE"] = value
    at = AppTest.from_file(app_path, default_timeout=60).run()
    texts = visible_texts(at)
    label = "<sin definir>" if value is None else "<ruta inválida>"
    print(
        f"   MODEL_UI_BUNDLE = {label} | inputs: {len(at.number_input)} | "
        f"excepciones: {len(at.exception)}"
    )
    for text in texts:
        print("   ", text)
    leaks = ("Traceback", "no-existe", "joblib", "C:\\")
    print("    ¿filtra ruta/traceback?", any(s in " ".join(texts) for s in leaks))
