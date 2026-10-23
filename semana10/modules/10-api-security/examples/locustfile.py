"""Demo S10 · Bloque 4 — Prueba de carga con Locust.

Arranca primero una demo en otra terminal, por ejemplo con un límite de 60/min:

    DEMO_API_KEY=demo-limits-key DEMO_RATE_LIMIT_PER_MINUTE=60 \\
      uv run fastapi dev examples/limits_demo.py

Y lanza 20 usuarios durante un minuto desde la raíz del módulo:

    LOCUST_API_KEY=demo-limits-key uv run --group load locust \\
      -f examples/locustfile.py --headless -u 20 -r 5 -t 1m \\
      --host http://127.0.0.1:8000

Sin `--headless`, Locust abre su interfaz en <http://localhost:8089>. Locust
cuenta cada `429` como fallo: el porcentaje de fallos de `POST /v1/scores` es
el porcentaje de peticiones que ha frenado el rate limit. Contra
`api_key_demo.py` (sin límite) usa `LOCUST_API_KEY=demo-front-key`.
"""

import os

from locust import HttpUser, between, task


class DemoUser(HttpUser):
    wait_time = between(0.5, 2)

    def on_start(self) -> None:
        # La clave llega por entorno, como en la API: nunca escrita en el script.
        self.client.headers["X-API-Key"] = os.environ["LOCUST_API_KEY"]

    @task(8)
    def score(self) -> None:
        self.client.post("/v1/scores", json={"age": 42, "income": 38000})

    @task(1)
    def health(self) -> None:
        self.client.get("/health")
