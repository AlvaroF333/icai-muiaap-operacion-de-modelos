import joblib

from app.config import MODEL_PATH
from app.schemas.prestamo import PrediccionSalida

# Orden en el que el modelo espera las variables
VARIABLES = [
    "edad",
    "ingresos_mensuales",
    "importe_prestamo",
    "plazo_meses",
    "antiguedad_laboral_anios",
    "impagos_previos",
]

UMBRAL_APROBAR = 0.2
UMBRAL_REVISAR = 0.5

# Se carga una sola vez, al importar el módulo: no en cada petición.
modelo = joblib.load(MODEL_PATH)


def decidir(probabilidad):
    if probabilidad < UMBRAL_APROBAR:
        return "aprobar"
    if probabilidad < UMBRAL_REVISAR:
        return "revisar"
    return "rechazar"


def predecir(entrada):
    """PrestamoEntrada -> PrediccionSalida (la salida también se valida con Pydantic)."""
    datos = entrada.model_dump()
    fila = [[datos[variable] for variable in VARIABLES]]
    probabilidad = float(modelo.predict_proba(fila)[0][1])
    return PrediccionSalida(probabilidad_impago=probabilidad, decision=decidir(probabilidad))
