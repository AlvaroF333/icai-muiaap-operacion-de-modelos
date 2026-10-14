import joblib
import pandas as pd
from pathlib import Path

# Cargar el modelo y los nombres esperados
model_path = Path(__file__).parent / "wine_quality_classifier.joblib"
model_data = joblib.load(model_path)

print(model_data)

model = model_data.get("estimator")
feature_names = model_data.get("feature_names")

# Ruta directa al CSV (está en la misma carpeta que este script)
csv_path = Path(__file__).parent / "WineQT.csv"
df = pd.read_csv(csv_path)

# Normalizar cabeceras a snake_case
df.columns = df.columns.str.lower().str.strip().str.replace(" ", "_")

# Extraer features y predecir
X = df[feature_names]
predictions = model.predict(X)

print("Predicciones:", predictions)
print(model)