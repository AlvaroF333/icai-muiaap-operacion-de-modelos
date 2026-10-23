# Operación de Modelos — MUIAAp

![Comillas ICAI](assets/comillas_logo.jpg)

Material docente de la asignatura **Operación de Modelos** del Máster
Universitario en Inteligencia Artificial Aplicada de Comillas ICAI.

La asignatura sigue un único proyecto incremental: llevar un modelo desde un
notebook experimental hasta una solución reproducible, validable, servible y
operable. Cada semana añade una capa al entregable anterior y deja una
evidencia que otra persona puede ejecutar y revisar.

## Recorrido de la asignatura

```text
prototipo → tracking → proyecto reproducible → inferencia local
          → bundle serializado → UI → API → contenedores
          → CI/CD → despliegue y monitorización
```

| Semana | Contenido principal | Assignment / entregable | Continuidad |
| --- | --- | --- | --- |
| [S1](semana1/) | Prototipo frente a producción, ciclo de vida de IA, MLflow, Databricks, AgentOps y LLMOps. | Entorno local preparado; después, runs trazables, gate, modelo registrado, API local y evaluación determinista. | La clase 1 prepara herramientas y acceso; la clase 2 inicia la evidencia técnica del proyecto. |
| [S2](semana2/) | Estructura de proyecto, entornos, dependencias y reproducibilidad con `uv`/Poetry. | Repositorio GitHub funcional, `README`, `pyproject`, lockfile, `.gitignore`, `src/`, tests y comando de arranque. | Convierte la ficha de S1 en un proyecto que otra persona puede clonar. |
| [S3](semana3/) | Inferencia, preprocesado y contratos de entrada/salida. | Módulo local de inferencia reutilizable, CLI/script y pruebas de casos válidos e inválidos. | Separa entrenamiento, artefacto, preprocesado e inferencia. |
| [S4](semana4/) | Serialización, manifiesto, formatos y validación de datos. | Bundle con `manifest.json` y `model.joblib`, carga segura, validación Pydantic y prueba de humo. | Empaqueta el módulo de S3 para que pueda consumirse sin conocer su interior. |
| [S5](semana5/) | Streamlit básico: caso Churn en clase 1 y transferencia conceptual a Wine en clase 2. | Miniapp Churn funcional y frontal Wine conectado obligatoriamente al bundle real de S4. | Practica formulario, submit y resultado antes de aplicar el patrón al proyecto. |
| [S6](semana6/) | Streamlit avanzado: `session_state`, caché, estados, errores, latencia, confianza y telemetría. | Evolución de la app de S5 con retry, clear, máquina de estados y telemetría sin payloads. | Hace robusto el consumo sin rehacer el formulario ni el contrato. |
| [S7](semana7/) | HTTP, REST, JSON, endpoints y códigos de estado. | Diseño de API: recursos, schemas, errores, secuencia de petición y cliente de prueba; inferencia desacoplada del front. | Sustituye el gateway local por una frontera de servicio bien definida. |
| [S8](semana8/) | FastAPI, rutas, schemas, validación y prueba con ngrok. | API REST funcional conectada al modelo y probada desde un cliente HTTP/front. | Implementa el diseño de S7. |
| [S9](semana9/) | Serialización avanzada, errores, tests y documentación OpenAPI. | API testeada, docstrings ricos, Swagger y respuestas de error consistentes. | Convierte la API funcional en una interfaz mantenible. |
| [S10](semana10/) | API keys/JWT, autorización, CORS, secrets, rate limiting y carga con Locust. | API protegida y prueba de controles de acceso y consumo. | Añade la seguridad mínima necesaria antes de contenerizar. |
| [S11](semana11/) | Dockerfile, imágenes, capas y contenedores. | Imagen ejecutable para back y front. | Empaqueta cada componente de S10 de forma portable. |
| [S12](semana12/) | Docker Compose, variables, redes y wiring front + API. | Stack local completo levantable desde un checkout limpio. | Integra las imágenes de S11 en un sistema reproducible. |
| [S13](semana13/) | DevOps/MLOps, CI/CD, tests, build, despliegue y monitorización. | Pipeline básico, evidencias de operación y presentación final, incluyendo model drift. | Cierra el ciclo de entrega y operación del proyecto. |

Las carpetas de S2 y S7–S13 contienen actualmente el marcador `.gitkeep`; sus
materiales se incorporarán manteniendo este mismo recorrido. Las semanas con
material ya disponible tienen su guía específica en el `README.md` de cada
carpeta.

## Handouts PDF de assignments

Las prácticas de las semanas con material desarrollado también están disponibles
como handouts independientes, separados por clase. Siguen una estructura de
assignment académico: objetivo, punto de partida, tareas, evidencias,
criterios de aceptación, rúbrica y comandos de comprobación. El formato toma
como referencia la organización de [CS336 Assignment 1 de Stanford](https://github.com/stanford-cs336/assignment1-basics/blob/main/cs336_assignment1_basics.pdf),
adaptada al proyecto incremental de esta asignatura.

| Semana | Clase 1 | Clase 2 |
| --- | --- | --- |
| S1 | [Assignment 1.1](assignments/semana01_clase01_assignment.pdf) | [Assignment 1.2](assignments/semana01_clase02_assignment.pdf) |
| S3 | [Assignment 3.1](assignments/semana03_clase01_assignment.pdf) | [Assignment 3.2](assignments/semana03_clase02_assignment.pdf) |
| S4 | [Assignment 4.1](assignments/semana04_clase01_assignment.pdf) | [Assignment 4.2](assignments/semana04_clase02_assignment.pdf) |
| S5 | [Assignment 5.1](assignments/semana05_clase01_assignment.pdf) | [Assignment 5.2](assignments/semana05_clase02_assignment.pdf) |
| S6 | [Assignment 6.1](assignments/semana06_clase01_assignment.pdf) | [Assignment 6.2](assignments/semana06_clase02_assignment.pdf) |
| S7 | [Assignment 7.1](assignments/semana07_clase01_assignment.pdf) | [Assignment 7.2](assignments/semana07_clase02_assignment.pdf) |
| S9 | [Assignment 9.1](assignments/semana09_clase01_assignment.pdf) | [Assignment 9.2](assignments/semana09_clase02_assignment.pdf) |

El PDF es la guía de trabajo para el alumno; el `README.md`, el `problem/`,
los tests y los `guides/` de cada semana siguen siendo la fuente de detalle
técnico y de preparación docente.

## Cómo interpretar el material

La estructura de una semana distingue claramente el material para preparar la
clase, el punto de partida del alumnado y la referencia docente.

| Ruta o archivo | Para el docente | Para el alumnado |
| --- | --- | --- |
| `semanaN/README.md` | Objetivo, secuencia, entregable y comandos de validación. | Punto de entrada: qué hay que aprender y qué hay que entregar. |
| `modules/.../README.md` | Mapa técnico de la unidad y decisiones pedagógicas. | Contexto del módulo y relación con las semanas anteriores. |
| `sessions/.../README.md` | Guion de cada clase y resultado esperado. | Orden de trabajo durante la sesión. |
| `guides/class-*.md` | Timing, preguntas, pistas y criterios de revisión. | No es la solución; sirve para entender la dinámica si se comparte. |
| `exercises/.../problem/` | Enunciado que se distribuye. | Punto de partida oficial: notebook sin resolver o proyecto `starter`. |
| `exercises/.../explainer/` | Hints y conceptos para el debrief. | Orientación para investigar sin copiar la solución. |
| `solutions/` | Referencia para demo, corrección y comparación. | Se consulta después de intentar la práctica y con autorización del docente. |
| `tests/`, `pyproject.toml`, `uv.lock` | Evidencia objetiva de comportamiento y reproducibilidad. | Comandos para comprobar que la entrega funciona desde un entorno limpio. |
| `assets/` y `examples/` | Dataset, muestras y ejemplos controlados. | Datos de prueba; no se deben sustituir contratos por valores inventados. |

Un `TODO` no significa “rellena cualquier código”: debe indicar una decisión,
una API o un invariante que falta. La entrega debe conservar la separación
entre datos, entrenamiento, modelo, inferencia, presentación y operación.

## Cómo hacer los assignments

Salvo que el README de una semana indique otra cosa, cada assignment se hace
con el siguiente ciclo:

1. Lee el objetivo de la semana y revisa el entregable que recibes de la
   semana anterior.
2. Abre únicamente `problem/` o el notebook sin resolver. Ejecuta primero el
   estado inicial para saber qué está preparado y qué falta.
3. Completa los `TODO` en el orden indicado. Mantén los contratos y nombres
   públicos de las semanas anteriores; si propones un cambio, documéntalo.
4. Comprueba casos normales y fallos controlados. No basta con una métrica o
   una captura de una ejecución correcta.
5. Ejecuta los tests, lint, formato o validación de notebook indicados en el
   README de la semana. Si una dependencia externa no está disponible,
   registra exactamente qué queda sin comprobar.
6. Entrega el artefacto ejecutable y una evidencia breve: comandos ejecutados,
   resultado, decisiones relevantes, limitaciones y siguiente paso.

### Assignment de cada semana

#### S1 — Operación observable

En la clase 1 prepara el entorno: instala `uv` con Python 3.12,
Git y, si usas Windows, Git Bash; configura tu identidad Git, confirma tu
cuenta GitHub y el acceso al repositorio, y verifica Databricks Free Edition
con el Git Folder y el *compute* serverless. Usa un navegador actualizado, un
editor con soporte para notebooks, `curl` y Postman para la práctica de HTTP.
Docker y Compose se revisan de forma anticipada, sin que su instalación bloquee
esta entrega. Entrega versiones, accesos y cualquier bloqueo sin compartir
secretos.

En la clase 2 trabaja en Databricks Free Edition con modo determinista cuando
sea posible. Ejecuta el notebook de tracking, registra parámetros, métricas,
artefactos y tags, aplica un gate sobre validación, reserva test para el
ganador, registra el modelo y prueba la API local. Después completa la traza y
evaluación de AgentOps/LLMOps sin pegar secretos. Entrega los identificadores
de runs, la regla del gate, riesgos observados y evidencias de éxito y error
de la API.

#### S2 — Proyecto reproducible

Crea el repositorio GitHub del proyecto de clase. Define el entorno con el
gestor acordado, fija dependencias, crea `src/`, tests y configuración, añade
un `README` de arranque y comprueba que otra persona puede clonar, instalar y
ejecutar un smoke test. El entregable no es sólo el repositorio: incluye el
comando de reproducción y las decisiones de estructura.

#### S3 — Inferencia local

Parte del prototipo y separa contrato, preprocesado, carga del artefacto y
predicción. Implementa el módulo o script de inferencia sobre `starter`, sin
entrenar dentro de la ruta de consumo. Valida entradas y salidas, prueba una
muestra válida y casos inválidos, y deja un comando reproducible que produzca
la salida esperada.

#### S4 — Bundle serializado

Construye el bundle a partir del módulo de S3. Guarda el estimador con
`joblib`, escribe un manifiesto legible con versiones, features y etiquetas,
valida el bundle antes de cargarlo y prueba la inferencia en un contexto nuevo.
Entrega `manifest.json`, `model.joblib` generado localmente, tests de
compatibilidad y una prueba de humo; no subas binarios ni secretos al
repositorio si el README de la semana los excluye.

#### S5 — Primera interfaz

Diseña primero la tabla de campos del formulario y luego completa el starter de
Streamlit. Reutiliza el gateway de S4, usa un formulario para enviar una
petición completa, presenta categoría, confianza y versiones, y muestra un
error básico sin traceback. Ejecuta la app con `DemoGateway` y, si está
disponible, con el bundle real. Conserva la app como snapshot para S6.

#### S6 — Interfaz robusta

No rehagas la app de S5. Sobre su snapshot añade estado idempotente, gateway
cacheado, transiciones `idle/loading/success/error`, reintento, limpieza,
políticas de confianza y latencia y telemetría agregada sin valores de entrada.
Prueba el éxito, el error de contrato, el bundle ausente y una respuesta lenta.
Entrega el diff de evolución y evidencias de que el resultado sobrevive a un
rerun.

#### S7 — Diseño de API

Convierte la frontera `InferenceGateway` en un contrato HTTP. Define endpoint,
método, JSON de entrada/salida, códigos de estado, errores y ejemplos de
petición. Dibuja la secuencia front → API → inferencia y elimina del diseño del
front cualquier dependencia directa del bundle. Prueba las peticiones con un
cliente HTTP; la implementación completa se realiza en S8.

#### S8 — API funcional

Implementa el diseño con FastAPI y schemas Pydantic. Expón la inferencia,
valida entradas, devuelve códigos HTTP coherentes y conecta el backend con el
artefacto de S4. Prueba la API local y, si el docente lo indica, publícala
temporalmente con ngrok sin incluir credenciales. Entrega código, ejemplos de
requests/responses y la evidencia de un caso válido y varios inválidos.

#### S9 — API profesionalizada

Añade tests de comportamiento, serialización estable, errores controlados,
docstrings y documentación OpenAPI. Comprueba que una salida inválida no llega
al cliente como un `200`, que los errores tienen estructura consistente y que
Swagger describe los schemas reales. Entrega la suite y una captura o export de
la documentación.

#### S10 — Seguridad y consumo

Protege los endpoints con API key o JWT según el alcance de la clase, configura
secrets fuera del código, define CORS explícitamente y añade rate limiting o
un control equivalente. Prueba acceso autorizado, no autorizado y exceso de
peticiones; usa Locust para observar el comportamiento bajo carga. No entregues
tokens reales: incluye sólo `.env.example` y resultados sanitizados.

#### S11 — Contenedores

Escribe y prueba un `Dockerfile` para el backend y otro para el frontend si
corresponde. Mantén explícitos el puerto, las dependencias, las variables y la
ruta del modelo; comprueba que cada imagen arranca desde un checkout limpio.
Entrega los Dockerfiles, comandos de build/run y una prueba de la aplicación
contenedorizada.

#### S12 — Stack local

Une front y API con `docker compose`. Define variables, red, puertos,
dependencias y health checks de forma explícita. Levanta el stack completo,
prueba el recorrido navegador → API → modelo y documenta cómo apagarlo y
arrancarlo de nuevo sin estado oculto.

#### S13 — Cierre operativo

Automatiza en CI/CD lint, tests, construcción de imagen y comprobaciones de
contrato. Explica el despliegue elegido y aporta evidencias, no afirmaciones.
Añade monitorización técnica y funcional, una señal de model drift y el plan de
respuesta. Entrega el repositorio final, el pipeline, el resumen de operación
y una presentación que conecte riesgos, decisiones y resultados.

## Regla de continuidad

Cada entrega debe poder responder tres preguntas:

- ¿Qué recibimos de la semana anterior y qué contrato se conserva?
- ¿Qué capacidad operativa nueva añadimos esta semana?
- ¿Qué evidencia demuestra que funciona y qué queda pendiente?

La carpeta `solutions/` sirve para el debrief docente; el assignment del
alumnado se corrige sobre el `starter`, sus tests y sus evidencias, no sobre la
solución de referencia.
