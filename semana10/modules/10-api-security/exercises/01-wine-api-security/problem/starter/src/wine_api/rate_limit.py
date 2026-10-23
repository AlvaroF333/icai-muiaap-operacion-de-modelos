"""Rate limiting por cliente con una ventana fija.

El contador vive en la memoria del proceso: sirve para un único worker y para
aprender. Con varios workers o réplicas cada uno contaría por su lado; en
producción el estado va a Redis o el límite lo aplica el API gateway.
"""

import logging
import math  # noqa: F401 - pista para S10.4b
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request, Response  # noqa: F401 - pista para S10.4c

from wine_api.security import ClientDep

logger = logging.getLogger("wine_api.rate_limit")


@dataclass(frozen=True)
class RateLimitDecision:
    """Resultado de contar una petición."""

    allowed: bool
    remaining: int
    retry_after: int


class FixedWindowRateLimiter:
    """Cuenta peticiones por clave en ventanas de `window_seconds`.

    `clock` es inyectable para que los tests avancen el tiempo sin esperar.
    `_windows` guarda, por clave, `(inicio de la ventana, peticiones contadas)`.
    """

    def __init__(
        self,
        window_seconds: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.window_seconds = window_seconds
        self.clock = clock
        self._windows: dict[str, tuple[float, int]] = {}
        # Las dependencias `def` corren en un threadpool: protege el contador.
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int) -> RateLimitDecision:
        """Cuenta una petición de `key` si cabe en su cuota de `limit`."""

        # TODO S10.4b: implementa la ventana fija dentro de `with self._lock:`.
        # - Si la ventana de `key` no existe o ya ha pasado `window_seconds`
        #   desde su inicio, empieza una nueva en `self.clock()`.
        # - Si ya hay `limit` peticiones, deniega SIN contar y calcula
        #   `retry_after`: segundos enteros que faltan para que acabe la
        #   ventana. ¿Por qué hay que redondear hacia arriba y no hacia abajo?
        # - Si cabe, cuenta la petición y devuelve cuántas quedan.
        # Usa `self.clock()`, nunca `time.time()`: así los tests controlan el
        # reloj. Mira `usage()` para ver cómo se lee `_windows`.
        # Comprobación: los tres primeros tests de tests/test_s10_4_rate_limit.py
        raise NotImplementedError("TODO S10.4b")

    def usage(self, key: str) -> int:
        """Peticiones contadas para `key` en la ventana actual."""

        with self._lock:
            start, count = self._windows.get(key, (0.0, 0))
            if self.clock() - start >= self.window_seconds:
                return 0
            return count


def get_rate_limiter(request: Request) -> FixedWindowRateLimiter:
    """Devuelve el limitador compartido por todas las peticiones del proceso."""

    return request.app.state.rate_limiter


RateLimiterDep = Annotated[FixedWindowRateLimiter, Depends(get_rate_limiter)]


def enforce_rate_limit(client: ClientDep, limiter: RateLimiterDep) -> None:
    """Cuenta la petición del cliente autenticado o lanza un `429`."""

    # TODO S10.4c: cuenta la petición con `limiter.hit(...)` usando el nombre
    # del cliente como clave y su `rate_limit_per_minute` como límite.
    # - Si no se permite, lanza `RateLimitExceededError` con `Retry-After`.
    # - Si se permite, añade a la respuesta `X-RateLimit-Limit` y
    #   `X-RateLimit-Remaining`. Investiga en la documentación de FastAPI
    #   «Response - Change Headers»: una dependencia también puede recibir
    #   `response: Response`.
    # ¿Por qué esta dependencia va DESPUÉS de autenticar y autorizar?
    # Comprobación: uv run pytest -q tests/test_s10_4_rate_limit.py
    raise NotImplementedError("TODO S10.4c")
