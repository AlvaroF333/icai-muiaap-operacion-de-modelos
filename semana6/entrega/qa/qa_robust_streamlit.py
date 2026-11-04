"""QA S6: recorre la app robusta con AppTest y guarda un registro de evidencia.

Ejecutar desde el starter (necesita el extra `app`):

    cd modules/06-ux-model-consumption/exercises/02-robust-streamlit/problem/starter
    uv sync --extra app
    uv run python ../../../../../../entrega/qa/qa_robust_streamlit.py

Recorridos: inicio, éxito, rerun, limpiar, bundle ausente, reintentar, salida
fuera de contrato y respuesta lenta con confianza baja.
"""

import json
from pathlib import Path

import streamlit as st
from model_ui import gateway as gateway_module
from streamlit.testing.v1 import AppTest

SEMANA6 = Path(__file__).resolve().parents[2]
APP = (
    SEMANA6
    / "modules/06-ux-model-consumption/exercises/02-robust-streamlit/problem/starter"
    / "app.py"
)
OUTPUT = SEMANA6 / "entrega/evidencia/recorridos.json"

# Cuenta cuántas veces se construye el gateway demo: con cache_resource debe
# ser una vez por escenario, no una por rerun.
builds = {"demo": 0}
original_init = gateway_module.DemoGateway.__init__


def counting_init(self, *args, **kwargs):
    builds["demo"] += 1
    original_init(self, *args, **kwargs)


gateway_module.DemoGateway.__init__ = counting_init
st.cache_resource.clear()
log: list[dict] = []


def texts(at: AppTest) -> list[str]:
    out = []
    for kind in ("info", "warning", "error", "success", "caption", "markdown"):
        out += [f"{kind}: {element.value}" for element in getattr(at, kind)]
    return out


def button(at: AppTest, label: str):
    return next(b for b in at.button if b.label == label)


def submit(at: AppTest) -> None:
    button(at, "Ejecutar inferencia").click().run()


def step(name: str, at: AppTest) -> dict:
    assert not at.exception, at.exception
    entry = {
        "paso": name,
        "metricas": {metric.label: metric.value for metric in at.metric},
        "mensajes": texts(at),
        "telemetria": json.loads(at.json[-1].value),
        "reintentar_habilitado": not button(at, "Reintentar").disabled,
        "limpiar_habilitado": not button(at, "Limpiar último resultado").disabled,
    }
    log.append(entry)
    return entry


def has(entry: dict, text: str) -> bool:
    return any(text in message for message in entry["mensajes"])


at = AppTest.from_file(str(APP), default_timeout=30)
at.run()
e = step("inicio", at)
assert has(e, "Introduce los valores") and e["metricas"] == {}

submit(at)
e = step("exito", at)
assert e["metricas"]["Categoría"] == "Resultado aceptable"
assert e["metricas"]["Confianza del modelo"] == "74%"
assert e["telemetria"]["requests_success"] == 1

at.run()
e = step("rerun", at)
assert e["metricas"]["Categoría"] == "Resultado aceptable", "resultado perdido"
assert builds["demo"] == 1, f"gateway reconstruido en el rerun: {builds}"

button(at, "Limpiar último resultado").click().run()
e = step("limpiar", at)
assert e["metricas"] == {} and has(e, "Introduce los valores")
assert e["telemetria"]["requests_total"] == 1, "limpiar borró la telemetría"

at.sidebar.selectbox[0].set_value("missing_bundle").run()
submit(at)
e = step("bundle_ausente", at)
assert has(e, "Modelo no disponible") and has(e, "Referencia de la petición")
assert e["reintentar_habilitado"]

button(at, "Reintentar").click().run()
e = step("reintentar", at)
assert e["telemetria"]["errors_by_code"] == {"artifact_unavailable": 2}

at.sidebar.selectbox[0].set_value("invalid_output").run()
submit(at)
e = step("salida_fuera_de_contrato", at)
assert has(e, "No se pudo obtener una predicción válida")

at.sidebar.selectbox[0].set_value("slow_low_confidence").run()
submit(at)
e = step("lenta_confianza_baja", at)
assert e["metricas"]["Categoría"] == "Requiere revisión"
assert has(e, "Confianza baja") and has(e, "Por encima del objetivo")
assert not e["reintentar_habilitado"], "un éxito lento no es un error"

# Privacidad: ni traceback en pantalla ni features/valores en la telemetría.
page = json.dumps(log, ensure_ascii=False)
assert "Traceback" not in page
for entry in log:
    telemetry_text = json.dumps(entry["telemetria"])
    for forbidden in ("fixed_acidity", "alcohol", "7.4", "0.9978"):
        assert forbidden not in telemetry_text, forbidden

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", "utf-8")
print(f"OK: {len(log)} recorridos verificados; DemoGateway construido", builds["demo"])
print(f"Registro: {OUTPUT.relative_to(SEMANA6).as_posix()}")
