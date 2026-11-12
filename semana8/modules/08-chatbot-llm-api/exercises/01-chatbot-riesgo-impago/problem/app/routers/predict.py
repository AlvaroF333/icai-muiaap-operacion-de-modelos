from fastapi import APIRouter

from app.schemas.prestamo import PrediccionSalida, PrestamoEntrada
from app.services.modelo import predecir

router = APIRouter()


@router.post("/predict", response_model=PrediccionSalida)
def predict(entrada: PrestamoEntrada) -> PrediccionSalida:
    """Predicción directa, sin LLM. Datos inválidos o campos inventados -> 422 (FastAPI)."""
    return predecir(entrada)
