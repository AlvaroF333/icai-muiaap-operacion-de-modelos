"""Dependencias compartidas por las rutas, sustituibles en los tests."""

from typing import Annotated

from fastapi import Depends, Request

from wine_api.predictor import Predictor
from wine_api.request_id import current_request_id
from wine_api.settings import Settings


def get_predictor(request: Request) -> Predictor:
    """Devuelve el predictor cargado una sola vez en el `lifespan`."""

    return request.app.state.predictor


def get_settings(request: Request) -> Settings:
    """Devuelve la configuración con la que se creó la aplicación."""

    return request.app.state.settings


PredictorDep = Annotated[Predictor, Depends(get_predictor)]
RequestIdDep = Annotated[str, Depends(current_request_id)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
