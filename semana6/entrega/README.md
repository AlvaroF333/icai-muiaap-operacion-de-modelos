# Entrega semana 6 — UX operable para consumir el modelo

| Assignment | Dónde está el trabajo |
| --- | --- |
| 6.1 Mapa de estado de la app de S5 | [Notebook de diseño](../modules/06-ux-model-consumption/exercises/01-ui-contract/problem/01-estado-streamlit-alumno.ipynb) (ejecutado) y cambio visual en [`ui_playground.py`](../modules/06-ux-model-consumption/exercises/01-ui-contract/problem/ui_playground.py) |
| 6.2 Evolución robusta de la interfaz de S5 | [Starter completado](../modules/06-ux-model-consumption/exercises/02-robust-streamlit/problem/starter/) |
| Evidencia de recorridos | [`qa/qa_robust_streamlit.py`](qa/qa_robust_streamlit.py) → [`evidencia/recorridos.json`](evidencia/recorridos.json) |

## 6.1 — Diseño (resumen)

El notebook contiene las cuatro evidencias que pide el assignment:

- **Contrato de sesión** (sección 2): `last_state: UiState`, `last_values: dict[str, float]`, `telemetry: Telemetry`; inicialización con `setdefault`; «Limpiar» borra `last_state` y `last_values` y conserva `telemetry`.
- **Máquina de estados** (sección 4): `idle → loading → success | error` con evento, zona, mensaje, acción permitida y evidencia, más la tabla de recuperación por código de error.
- **Decisión de caché** (sección 7): se cachea el gateway con `st.cache_resource`; argumento de caché `bundle_value` (y el escenario docente); excluidos los valores y las respuestas de cada persona.
- **Plan de implementación** (sección 8): requisito → archivo y función → test del starter.

Limitación observable de S5 de la que parte el diseño: el resultado solo existe dentro de `if submitted` (desaparece en el siguiente rerun) y el gateway se reconstruye en cada rerun.

## 6.2 — Diff de evolución

**Se conserva de S5, sin cambios:** `FEATURE_FIELDS` (11 campos), `collect_values()`, `gateway.py` (`DemoGateway`, `UnavailableGateway`, `PackagedBundleGateway` y la validación de nombres), `contracts.py`, `telemetry.py`, `errors.py` y todos los tests.

**Se añade en S6:**

| Archivo | Cambio |
| --- | --- |
| `session.py` | Inicialización idempotente con `setdefault`; `clear_last_state` vuelve a `idle` sin tocar la telemetría. |
| `policies.py` | Confianza `< 0.60` low, `>= 0.85` high, resto medium (fuera de `[0, 1]` → `ValueError`); latencia `<= 300 ms` within_target. |
| `presentation.py` | `build_prediction_view` (etiquetas, copy, versiones y mensaje de latencia con el objetivo); `to_user_facing_error` con copy estable por código, que nunca reutiliza el texto de la excepción. |
| `controller.py` | `submit`: crea `request_id`, emite `loading`, mide la latencia del gateway, **revalida la salida** con `PredictionPayload`, traduce cualquier excepción, registra solo agregados y emite `success`/`error`. Log del servidor con `request_id`, código y clase de excepción (sin payload). |
| `app.py` | `get_cached_gateway` con `st.cache_resource`; `render_state` sobre un `st.empty` reservado (3 `st.metric`, `st.warning`/`st.info`, `st.expander` de trazabilidad, error con recuperación y `request_id`); `st.status` para la operación; «Reintentar» (deshabilitado salvo error recuperable, e invalida la caché tras `artifact_unavailable`) y «Limpiar» (callback `on_click`). Selector lateral de escenarios docentes cuando no hay `MODEL_UI_BUNDLE`. |

Objeto cacheado: el gateway, que contiene el bundle de S4 y su adaptador; es igual para todas las sesiones y su `predict` no guarda nada de la petición. Las respuestas viven en `st.session_state`.

Se conserva para S7: `PredictionController`, las políticas, la vista y `render_state` no dependen del gateway concreto; basta con un `InferenceGateway` HTTP que devuelva JSON (el controlador ya revalida dicts con `PredictionPayload`).

## Comprobación

```bash
cd semana6/modules/06-ux-model-consumption/exercises/02-robust-streamlit/problem/starter
uv sync --extra app
uv run pytest                      # 8 passed
uv run ruff check src tests        # All checks passed
uv run ruff format --check src tests
uv run python ../../../../../../entrega/qa/qa_robust_streamlit.py   # 8 recorridos OK
uv run streamlit run app.py
```

Para usar el bundle real de S4/S5 en lugar del gateway demo:

```bash
MODEL_UI_BUNDLE=../../../../../../../semana5/models/wine_quality_bundle uv run streamlit run app.py
```

## Evidencia de recorridos

[`evidencia/recorridos.json`](evidencia/recorridos.json) registra, para cada paso, las métricas visibles, los mensajes, la telemetría y si «Reintentar»/«Limpiar» están habilitados:

| Recorrido | Qué se comprueba |
| --- | --- |
| inicio | Instrucción en `idle`, sin métricas vacías. |
| exito | Categoría, confianza (74 %) y latencia; versiones en la trazabilidad. |
| rerun | El resultado sigue visible y el gateway no se reconstruye (1 construcción). |
| limpiar | Vuelve a `idle`; `requests_total` se mantiene. |
| bundle_ausente | «Modelo no disponible», recuperación y `request_id`; sin ruta interna. |
| reintentar | Reenvía `last_values`; `errors_by_code.artifact_unavailable` = 2. |
| salida_fuera_de_contrato | El controlador rechaza una salida inválida → `prediction_error`. |
| lenta_confianza_baja | Sigue en `success` con avisos de confianza baja y de latencia (800 ms > 300 ms). |

En ningún paso aparece un traceback ni valores de las features en la telemetría.

Capturas de pantalla: hay que tomarlas a mano desde `uv run streamlit run app.py`, usando el selector «Escenario de demostración» de la barra lateral para los estados de éxito, error, reintento y limpieza.
