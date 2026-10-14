"""Preprocesado reproducible de una muestra validada en el vector del modelo."""

from dataclasses import dataclass

from model_inference.contracts import WineQualityRequest

PREPROCESSING_VERSION = "wine-red-features-v1"

# Este contrato se entrega ya decidido: no cambies ni los nombres ni el orden.
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
    """Vector de características en el orden que usó el entrenamiento.

    Cada atributo se almacena como float y ``as_vector()`` devuelve la
    lista numérica en el mismo orden que ``FEATURE_NAMES``.
    """

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
        """Devuelve una lista numérica ordenada para el clasificador cargado."""

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
    """Convierte el contrato de entrada en el vector del modelo entrenado.

    Usa ``model_dump()`` para extraer los campos validados y los pasa
    al dataclass en el orden definido por ``FEATURE_NAMES``.
    """

    return WineFeatures(**request.model_dump())
