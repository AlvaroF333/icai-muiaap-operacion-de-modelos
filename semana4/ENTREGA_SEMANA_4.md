# Entrega Semana 4 — Operación de Modelos (MUIAAp)

**Asignatura:** Operación de Modelos  
**Máster:** Máster Universitario en Inteligencia Artificial Aplicada (MUIAAp) — Comillas ICAI  
**Semana:** 4 — Serialización, manifiesto y validación de modelos  
**Alumno:** Álvaro Figueroa Plaza  

---

## 1. Resumen de la entrega

Esta entrega implementa la frontera de empaquetado y consumo reproducible de modelos de Machine Learning correspondiente a la **Semana 4**, cubriendo la totalidad de los objetivos de:
- **Assignment 4.1 (`semana04_clase01_assignment.pdf`):** Contrato del artefacto, diseño de frontera, manifiesto y matriz de invariantes.
- **Assignment 4.2 (`semana04_clase02_assignment.pdf`):** Bundle serializado (`manifest.json` + `model.joblib`), guardado/carga validados, inferencia tipada y CLI con salida atómica.

El material está preparado para ser revisado y ejecutado directamente desde:
- `semana4/modules/04-model-packaging/exercises/01-model-packaging/01.01-artifact-contract/problem/01-artefacto-y-manifiesto-alumno.ipynb` (Notebook de Clase 1 completo y ejecutado).
- `semana4/solucionSemana4/` (Módulo local ejecutable de Clase 2 con tests y CLI).
- `semana4/modules/04-model-packaging/exercises/01-model-packaging/01.02-serializable-inference-module/problem/starter/` (Starter con la implementación completa).

---

## 2. Evidencias Clase 1 (Assignment 4.1: Contrato del artefacto y manifiesto)

### 2.1. Tabla de almacenamiento y justificación de frontera

| Elemento | ¿Dónde vive? | Justificación y riesgo que evita |
| :--- | :--- | :--- |
| **Estimador entrenado** | `model.joblib` | Evita reentrenar en cada inferencia y depender de código de ajuste; encapsula los pesos aprendidos y la lógica algorítmica para predecir (`predict` / `predict_proba`). |
| **Versión del esquema** | `manifest.json` (`schema_version`) | Evita incompatibilidades estructurales; impide que un cargador consuma bundles con especificación de metadatos diferente o incompatible. |
| **Orden y nombres de features** | `manifest.json` (`feature_names`) | Evita la corrupción silenciosa de datos (*silent data corruption*); garantiza que las columnas del vector de entrada coincidan en nombre, cantidad y orden con lo esperado por el modelo. |
| **Versión del preprocesado** | `manifest.json` (`preprocessing_version`) | Evita discrepancias matemáticas entre el preprocesado/vectorizado en inferencia y el utilizado en entrenamiento. |
| **Etiquetas de salida permitidas** | `manifest.json` (`output_labels`) | Evita que el modelo retorne clases no contempladas por el contrato del consumidor (dashboard, API REST). |
| **Versión del modelo** | `manifest.json` (`model_version`) | Garantiza la trazabilidad, linaje y auditoría del modelo desplegado respecto a los experimentos previos. |
| **Tipo de estimador** | `manifest.json` (`estimator_type`) | Permite inspeccionar qué algoritmo/clase (`RandomForestClassifier`, etc.) se empaquetó sin deserializar el binario, comprobando la compatibilidad de interfaz. |

### 2.2. Manifiesto propuesto (`manifest.json`)

Contrato estricto con las 6 claves obligatorias (`extra="forbid"`) y valores coherentes con la Semana 3:

```json
{
  "schema_version": "wine-quality-bundle-v1",
  "model_version": "wine-quality-rf-demo-v1",
  "preprocessing_version": "wine-red-features-v1",
  "feature_names": [
    "fixed_acidity",
    "volatile_acidity",
    "citric_acid",
    "residual_sugar",
    "chlorides",
    "free_sulfur_dioxide",
    "total_sulfur_dioxide",
    "density",
    "ph",
    "sulphates",
    "alcohol"
  ],
  "output_labels": [
    "needs_review",
    "acceptable",
    "excellent"
  ],
  "estimator_type": "RandomForestClassifier"
}
```

### 2.3. Matriz de invariantes y anticipación de fallos

| Cambio / Evento | Frontera que debe rechazarlo | Error y mensaje esperado | ¿Se escribe CSV? |
| :--- | :--- | :--- | :---: |
| **Se intercambian `density` y `alcohol`** | Validación de manifiesto (`load_model_bundle` / `ArtifactManifest`) | `ValueError: feature_names no coincide con el orden del contrato.` | **No** |
| **Cambia `preprocessing_version`** | Validación de manifiesto (`load_model_bundle` / `ArtifactManifest`) | `ValueError: preprocessing_version incompatible: se esperaba wine-red-features-v1.` | **No** |
| **El modelo devuelve `unknown`** | Validación de salida (`infer_wine_quality`) | `ValueError: Etiqueta de inferencia desconocida o no permitida: unknown.` | **No** |
| **La petición incluye `ph = 99`** | Validación de contrato de entrada (`WineQualityRequest`) | `ValueError / ValidationError: Input should be less than or equal to 4.5.` | **No** |
| **Falta `manifest.json`** | Validación previa a la carga (`load_model_bundle`) | `ValueError: No se encuentra el manifiesto en ...` | **No** |
| **Manifest con sintaxis corrupta** | Validación JSON (`load_model_bundle`) | `ValueError: Manifiesto inválido en ...` | **No** |
| **Estimador sin `predict_proba`** | Validación de interfaz (`_require_estimator`) | `ValueError: El estimador debe exponer predict y predict_proba.` | **No** |

### 2.4. Política de errores y atomicidad

- **Lectura y acumulación en memoria:** El CLI lee y valida el CSV de entrada fila a fila en memoria.
- **Salida atómica todo-o-nada:** Si cualquier fila viola el contrato de entrada o la inferencia falla, el proceso aborta inmediatamente elevando el error y descartando el buffer acumulado. El archivo de salida nunca se abre ni se crea, garantizando que jamás se publique una salida parcial o inconsistente.

---

## 3. Evidencias Clase 2 (Assignment 4.2: Bundle serializado y CLI validado)

### 3.1. Estructura del bundle generado

```text
models/wine_quality_bundle/
├── manifest.json       # Metadatos estrictos y validables
└── model.joblib        # Estimador serializado (DummyClassifier)
```

### 3.2. Nota de compatibilidad: Dos ejemplos de cambios bloqueados

1. **Alteración del orden de `feature_names`:**
   - *Riesgo:* Si un bundle alterara el orden de las columnas (por ejemplo, intercambiando `density` en posición 7 y `alcohol` en posición 10), el preprocesado alimentaría al modelo con valores de densidad (~0.99) en lugar de alcohol (~9.4–14.0).
   - *Mecanismo de bloqueo:* `ArtifactManifest.validate_feature_names` y `load_model_bundle` comparan estrictamente la tupla contra `FEATURE_NAMES` de la Semana 3 antes de permitir cualquier inferencia, impidiendo la corrupción silenciosa de datos (*silent data corruption*).

2. **Incompatibilidad de `preprocessing_version` y etiquetas de salida (`output_labels`):**
   - *Riesgo:* Si el preprocesado cambia el escalado matemático o el modelo genera etiquetas no contempladas (ej. `unknown`, `bad`, o `high`), la respuesta rompería la API o el dashboard aguas abajo.
   - *Mecanismo de bloqueo:* El manifiesto fija `preprocessing_version = "wine-red-features-v1"` y `output_labels = ("needs_review", "acceptable", "excellent")`. La función `infer_wine_quality` comprueba que cada predicción pertenezca taxativamente a `output_labels` antes de retornar el objeto `WineQualityPrediction`.

---

## 4. Instrucciones de reproducción y verificación

Para verificar la solución completa de forma limpia:

### 4.1. Verificación del módulo y suite de tests

```bash
# Entrar a la solución de la semana 4
cd semana4/solucionSemana4

# Sincronizar dependencias
uv sync

# Ejecutar la suite completa de tests (11 tests pasando)
uv run pytest

# Verificación de estilo y tipado con Ruff
uv run ruff check src tests
uv run ruff format --check src tests
```

### 4.2. Ejecución del CLI de inferencia

```bash
uv run python -m model_packaging.predict_file \
  --bundle models/wine_quality_bundle \
  --input ../../semana3/assets/03-wine-quality/inference_samples.csv \
  --output .tmp/wine_predictions.csv
```

Salida producida (`.tmp/wine_predictions.csv`):
```csv
sample_id,quality_band,confidence,model_version,preprocessing_version
red-001,acceptable,1.0,wine-quality-dummy-v1,wine-red-features-v1
red-002,acceptable,1.0,wine-quality-dummy-v1,wine-red-features-v1
red-003,acceptable,1.0,wine-quality-dummy-v1,wine-red-features-v1
red-004,acceptable,1.0,wine-quality-dummy-v1,wine-red-features-v1
red-005,acceptable,1.0,wine-quality-dummy-v1,wine-red-features-v1
```

### 4.3. Verificación del Notebook (Clase 1)

El notebook guiado se encuentra completado y con todas las celdas ejecutadas en:
`semana4/modules/04-model-packaging/exercises/01-model-packaging/01.01-artifact-contract/problem/01-artefacto-y-manifiesto-alumno.ipynb`
