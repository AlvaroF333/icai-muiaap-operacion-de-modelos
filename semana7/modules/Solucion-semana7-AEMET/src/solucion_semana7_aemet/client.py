"""Cliente de la API AEMET OpenData construido con ``requests``.

La API de AEMET funciona en DOS PASOS para cada consulta:

1. Se llama al endpoint documentado (p. ej. inventario de estaciones) pasando la
   API key como query string ``api_key``. La respuesta NO trae los datos, sino un
   JSON "sobre" con este contrato::

       {"descripcion": "exito", "estado": 200,
        "datos": "https://opendata.aemet.es/opendata/sh/...",
        "metadatos": "https://opendata.aemet.es/opendata/sh/..."}

2. Se hace un GET a la URL de ``datos`` para descargar el JSON real.

Ojo: el campo ``estado`` del sobre puede indicar error (401, 404, 429...) aunque
el código HTTP sea 200, así que se comprueban ambos.
"""

from __future__ import annotations

import time
from typing import Any

import requests

BASE_URL = "https://opendata.aemet.es/opendata/api"
INVENTARIO_PATH = "/valores/climatologicos/inventarioestaciones/todasestaciones"
DIARIOS_PATH = (
    "/valores/climatologicos/diarios/datos"
    "/fechaini/{fechaIniStr}/fechafin/{fechaFinStr}/estacion/{idema}"
)


class AemetError(RuntimeError):
    """Error de negocio o de transporte al hablar con AEMET."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class AemetClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_seconds: float = 2.0,
        session: requests.Session | None = None,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("Falta la API key de AEMET (variable API_AEMET).")
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.session = session or requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    # ------------------------------------------------------------------ HTTP
    def _get(self, url: str, params: dict[str, str] | None = None) -> requests.Response:
        """GET con timeout y reintentos ante 429 (rate limit) y 5xx."""
        last_exc: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, params=params, timeout=self.timeout)
            except (requests.ConnectionError, requests.Timeout) as exc:
                last_exc = exc
            else:
                if resp.status_code == 429 or resp.status_code >= 500:
                    last_exc = AemetError(
                        f"HTTP {resp.status_code} en {url}", resp.status_code
                    )
                else:
                    return resp
            if attempt < self.max_retries:
                time.sleep(self.backoff_seconds * attempt)
        raise AemetError(f"Fallo tras {self.max_retries} intentos: {last_exc}")

    def _request_envelope(self, path: str) -> dict[str, Any]:
        """Paso 1: llama al endpoint con ``api_key`` y valida el sobre."""
        resp = self._get(f"{self.base_url}{path}", params={"api_key": self.api_key})
        if resp.status_code == 401:
            raise AemetError("API key no válida o caducada (HTTP 401).", 401)
        if resp.status_code != 200:
            raise AemetError(
                f"HTTP {resp.status_code}: {resp.text[:200]}", resp.status_code
            )
        try:
            envelope = resp.json()
        except ValueError as exc:
            raise AemetError("La respuesta de AEMET no es JSON válido.") from exc

        estado = envelope.get("estado")
        if estado != 200 or "datos" not in envelope:
            raise AemetError(
                f"AEMET respondió estado={estado}: {envelope.get('descripcion')}",
                estado,
            )
        return envelope

    def _download_datos(self, datos_url: str) -> list[dict[str, Any]]:
        """Paso 2: descarga el JSON real desde la URL temporal ``datos``."""
        resp = self._get(datos_url)
        if resp.status_code != 200:
            raise AemetError(
                f"HTTP {resp.status_code} al descargar datos", resp.status_code
            )
        # AEMET sirve los datos en ISO-8859-15 sin declararlo bien: si se deja a
        # requests adivinar, los nombres con tildes/eñes salen corruptos.
        resp.encoding = "ISO-8859-15"
        try:
            data = resp.json()
        except ValueError as exc:
            raise AemetError("El fichero de datos no es JSON válido.") from exc
        if not isinstance(data, list):
            raise AemetError(f"Se esperaba una lista y llegó {type(data).__name__}.")
        return data

    def _fetch(self, path: str) -> list[dict[str, Any]]:
        envelope = self._request_envelope(path)
        return self._download_datos(envelope["datos"])

    # ------------------------------------------------------------ Endpoints
    def inventario_estaciones(self) -> list[dict[str, Any]]:
        """Inventario completo de estaciones climatológicas."""
        return self._fetch(INVENTARIO_PATH)

    def buscar_idema(self, nombre: str) -> str:
        """Devuelve el ``indicativo`` (idema) de la estación con ese nombre."""
        objetivo = nombre.strip().upper()
        estaciones = self.inventario_estaciones()
        coincidencias = [
            e for e in estaciones if e.get("nombre", "").strip().upper() == objetivo
        ]
        if not coincidencias:
            raise AemetError(f"No existe ninguna estación llamada {nombre!r}.")
        if len(coincidencias) > 1:
            ids = [e.get("indicativo") for e in coincidencias]
            raise AemetError(f"Nombre ambiguo {nombre!r}: {ids}")
        return coincidencias[0]["indicativo"]

    def climatologia_diaria(
        self, fecha_ini: str, fecha_fin: str, idema: str
    ) -> list[dict[str, Any]]:
        """Valores climatológicos diarios de una estación entre dos fechas.

        Las fechas van en formato AEMET ``AAAA-MM-DDTHH:MM:SSUTC``.
        """
        path = DIARIOS_PATH.format(
            fechaIniStr=fecha_ini, fechaFinStr=fecha_fin, idema=idema
        )
        return self._fetch(path)
