from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

EDAD_MINIMA_LABORAL = 16


class PrestamoEntrada(BaseModel):
    """Datos de una solicitud de préstamo: contrato único de /predict y de la tool del LLM."""

    # extra="forbid": si el LLM (o un cliente) se inventa un campo, se rechaza.
    model_config = ConfigDict(extra="forbid")

    edad: int = Field(ge=18, le=75, description="Edad del solicitante en años")
    ingresos_mensuales: float = Field(gt=0, description="Ingresos netos mensuales en euros")
    importe_prestamo: float = Field(gt=0, description="Importe solicitado en euros")
    plazo_meses: int = Field(ge=6, le=84, description="Plazo de devolución en meses")
    antiguedad_laboral_anios: int = Field(
        ge=0, le=50, description="Años en el empleo actual (como mucho edad - 16)"
    )
    impagos_previos: int = Field(ge=0, le=20, description="Número de impagos anteriores")

    @field_validator("antiguedad_laboral_anios")
    @classmethod
    def antiguedad_coherente_con_edad(cls, valor: int, info: ValidationInfo) -> int:
        # edad se valida antes (se declara antes); si era inválida no está en info.data
        edad = info.data.get("edad")
        if edad is not None and valor > edad - EDAD_MINIMA_LABORAL:
            raise ValueError(
                f"la antigüedad laboral ({valor}) no puede superar edad - "
                f"{EDAD_MINIMA_LABORAL} ({edad - EDAD_MINIMA_LABORAL})"
            )
        return valor


class PrediccionSalida(BaseModel):
    probabilidad_impago: float = Field(ge=0, le=1)
    decision: Literal["aprobar", "revisar", "rechazar"]
