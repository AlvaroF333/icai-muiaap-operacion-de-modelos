"""Preprocesado entregado desde la semana 3."""

from dataclasses import dataclass

from model_packaging.contracts import WineQualityRequest

PREPROCESSING_VERSION = "wine-red-features-v1"

FEATURE_NAMES = (
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
    "alcohol",
)


@dataclass(frozen=True)
class WineFeatures:
    """Vector de características en el orden estable del modelo."""

    fixed_acidity: float
    volatile_acidity: float
    citric_acid: float
    residual_sugar: float
    chlorides: float
    free_sulfur_dioxide: float
    total_sulfur_dioxide: float
    density: float
    ph: float
    sulphates: float
    alcohol: float

    def as_vector(self) -> list[float]:
        """Devuelve las once medidas en el orden acordado."""

        return [
            self.fixed_acidity,
            self.volatile_acidity,
            self.citric_acid,
            self.residual_sugar,
            self.chlorides,
            self.free_sulfur_dioxide,
            self.total_sulfur_dioxide,
            self.density,
            self.ph,
            self.sulphates,
            self.alcohol,
        ]


def preprocess_wine_request(request: WineQualityRequest) -> WineFeatures:
    """Construye el vector que espera el estimador."""

    return WineFeatures(**request.model_dump())
