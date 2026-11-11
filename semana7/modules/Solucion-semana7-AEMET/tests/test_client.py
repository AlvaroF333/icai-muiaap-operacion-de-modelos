"""Tests sin red: se sustituye la ``requests.Session`` por un doble."""

from __future__ import annotations

import json

import pytest
import requests

from solucion_semana7_aemet.client import BASE_URL, AemetClient, AemetError
from solucion_semana7_aemet.transform import to_dataframe

DATOS_INV = "https://opendata.aemet.es/opendata/sh/inv"
DATOS_DIA = "https://opendata.aemet.es/opendata/sh/dia"

INVENTARIO = [
    {"indicativo": "3195", "nombre": "MADRID, RETIRO", "provincia": "MADRID"},
    {
        "indicativo": "3194U",
        "nombre": "MADRID, CIUDAD UNIVERSITARIA",
        "provincia": "MADRID",
    },
]
DIARIOS = [
    {
        "fecha": "2019-10-02",
        "indicativo": "3194U",
        "tmed": "16,0",
        "prec": "Ip",
        "tmin": "10,1",
        "tmax": "21,9",
    },
    {
        "fecha": "2019-10-01",
        "indicativo": "3194U",
        "tmed": "18,4",
        "prec": "0,0",
        "tmin": "12,3",
        "tmax": "24,5",
    },
]


def make_response(status: int, payload, encoding: str = "utf-8") -> requests.Response:
    resp = requests.Response()
    resp.status_code = status
    resp._content = json.dumps(payload, ensure_ascii=False).encode(encoding)
    return resp


def envelope(datos_url: str, estado: int = 200) -> dict:
    return {
        "descripcion": "exito",
        "estado": estado,
        "datos": datos_url,
        "metadatos": datos_url + "/meta",
    }


class FakeSession:
    """Devuelve respuestas según la URL y registra cada llamada."""

    def __init__(self, routes: dict[str, list[requests.Response]]):
        self.routes = routes
        self.calls: list[tuple[str, dict | None]] = []
        self.headers: dict[str, str] = {}

    def get(self, url, params=None, timeout=None):
        assert timeout is not None, "toda petición debe llevar timeout"
        self.calls.append((url, params))
        return self.routes[url].pop(0)


def client_with(routes) -> tuple[AemetClient, FakeSession]:
    session = FakeSession(routes)
    client = AemetClient("KEY", session=session, backoff_seconds=0)
    return client, session


INV_URL = f"{BASE_URL}/valores/climatologicos/inventarioestaciones/todasestaciones"
DIA_URL = (
    f"{BASE_URL}/valores/climatologicos/diarios/datos/fechaini/"
    "2019-10-01T00:00:00UTC/fechafin/2019-10-30T23:59:59UTC/estacion/3194U"
)


def test_api_key_obligatoria():
    with pytest.raises(ValueError):
        AemetClient("  ")


def test_buscar_idema_flujo_dos_pasos_y_api_key_en_query():
    client, session = client_with(
        {
            INV_URL: [make_response(200, envelope(DATOS_INV))],
            DATOS_INV: [make_response(200, INVENTARIO, encoding="iso-8859-15")],
        }
    )
    assert client.buscar_idema("Madrid, Ciudad Universitaria") == "3194U"
    assert session.calls[0] == (INV_URL, {"api_key": "KEY"})
    assert session.calls[1][0] == DATOS_INV


def test_climatologia_url_con_fechas_e_idema():
    client, session = client_with(
        {
            DIA_URL: [make_response(200, envelope(DATOS_DIA))],
            DATOS_DIA: [make_response(200, DIARIOS)],
        }
    )
    datos = client.climatologia_diaria(
        "2019-10-01T00:00:00UTC", "2019-10-30T23:59:59UTC", "3194U"
    )
    assert len(datos) == 2
    assert session.calls[0] == (DIA_URL, {"api_key": "KEY"})


def test_estado_de_error_en_el_sobre_aunque_http_sea_200():
    client, _ = client_with(
        {
            INV_URL: [
                make_response(200, {"descripcion": "No hay datos", "estado": 404})
            ],
        }
    )
    with pytest.raises(AemetError) as exc:
        client.inventario_estaciones()
    assert exc.value.status == 404


def test_api_key_invalida_401():
    client, _ = client_with({INV_URL: [make_response(401, {"estado": 401})]})
    with pytest.raises(AemetError, match="401"):
        client.inventario_estaciones()


def test_reintenta_ante_429():
    client, session = client_with(
        {
            INV_URL: [make_response(429, {}), make_response(200, envelope(DATOS_INV))],
            DATOS_INV: [make_response(200, INVENTARIO)],
        }
    )
    assert len(client.inventario_estaciones()) == 2
    assert [u for u, _ in session.calls].count(INV_URL) == 2


def test_estacion_inexistente():
    client, _ = client_with(
        {
            INV_URL: [make_response(200, envelope(DATOS_INV))],
            DATOS_INV: [make_response(200, INVENTARIO)],
        }
    )
    with pytest.raises(AemetError, match="No existe"):
        client.buscar_idema("ESTACION FANTASMA")


def test_to_dataframe_tipos_y_orden():
    df = to_dataframe(DIARIOS)
    assert list(df["fecha"].dt.day) == [1, 2]
    assert df["tmed"].dtype == "float64"
    assert df.loc[0, "tmax"] == pytest.approx(24.5)
    assert df.loc[1, "prec"] == 0.0  # "Ip" -> 0.0
