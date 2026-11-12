import json

from pydantic import ValidationError

from app.schemas.chat import ChatSalida, HerramientaUsada
from app.schemas.prestamo import PrestamoEntrada
from app.services.modelo import predecir

NOMBRE_TOOL = "calcular_riesgo_impago"
MAX_VUELTAS = 4

SISTEMA = (
    "Eres un asistente de riesgo de un banco. Cuando tengas todos los datos de una solicitud de "
    "prestamo, llama a la herramienta calcular_riesgo_impago. Si falta algun dato, pidelo. "
    "Nunca inventes valores. Responde en espanol y de forma breve."
)


def leer_argumentos(texto):
    """YA HECHO: convierte el texto JSON de la tool en dict ({} si no es JSON valido)."""
    try:
        datos = json.loads(texto)
    except (json.JSONDecodeError, TypeError):
        return {}
    if isinstance(datos, dict):
        return datos
    return {}


def definir_tool():
    """Definición de la tool en formato OpenAI. Los parameters salen de PrestamoEntrada:
    un único contrato para /predict y para el LLM (si cambia el schema, cambia la tool)."""
    return {
        "type": "function",
        "function": {
            "name": NOMBRE_TOOL,
            "description": (
                "Calcula la probabilidad de impago de una solicitud de prestamo y la "
                "decision (aprobar, revisar o rechazar). Requiere los seis datos."
            ),
            "parameters": PrestamoEntrada.model_json_schema(),
        },
    }


def _formatear_errores(error):
    """ValidationError -> texto corto que el LLM entiende ('edad: ...; saldo_cuenta: ...')."""
    partes = []
    for e in error.errors():
        campo = ".".join(str(p) for p in e["loc"]) or "entrada"
        partes.append(f"{campo}: {e['msg']}")
    return "Datos no validos -> " + "; ".join(partes)


def ejecutar_tool(nombre, argumentos_json):
    """Ejecuta la tool. NUNCA lanza excepción: devuelve {"ok": True, ...} o {"ok": False, "error": ...}
    para que el LLM pueda corregirse o pedir el dato al usuario."""
    if nombre != NOMBRE_TOOL:
        return {"ok": False, "error": f"Herramienta desconocida: {nombre}"}
    argumentos = leer_argumentos(argumentos_json)
    if not argumentos:
        return {"ok": False, "error": "Los argumentos no son un objeto JSON valido."}
    try:
        entrada = PrestamoEntrada(**argumentos)
    except ValidationError as error:
        return {"ok": False, "error": _formatear_errores(error)}
    try:
        salida = predecir(entrada)
    except Exception as error:  # fallo del modelo: se informa, no se propaga
        return {"ok": False, "error": f"Error al ejecutar el modelo: {error}"}
    return {"ok": True, **salida.model_dump()}


def responder(mensajes, llm):
    """Bucle LLM -> tool -> LLM. Como mucho MAX_VUELTAS llamadas al LLM."""
    historial = [{"role": "system", "content": SISTEMA}]
    historial += [m.model_dump() for m in mensajes]
    herramientas = [definir_tool()]
    herramienta_usada = None

    for _ in range(MAX_VUELTAS):
        respuesta = llm.completar(historial, herramientas)
        llamadas = respuesta.get("tool_calls") or []

        if not llamadas:  # el LLM contesta con texto: fin
            return ChatSalida(respuesta=respuesta.get("content") or "", herramienta=herramienta_usada)

        historial.append(respuesta)  # el mensaje del asistente con tool_calls va al historial
        for llamada in llamadas:
            nombre = llamada["function"]["name"]
            argumentos_json = llamada["function"]["arguments"]
            resultado = ejecutar_tool(nombre, argumentos_json)
            herramienta_usada = HerramientaUsada(
                nombre=nombre, argumentos=leer_argumentos(argumentos_json), resultado=resultado
            )
            historial.append(
                {
                    "role": "tool",
                    "tool_call_id": llamada.get("id", ""),
                    "content": json.dumps(resultado, ensure_ascii=False),
                }
            )

    # Se agotaron las vueltas sin respuesta de texto: se corta el bucle con un mensaje claro.
    return ChatSalida(
        respuesta=(
            "No he podido completar el calculo tras varios intentos. "
            "Revisa los datos de la solicitud e intentalo de nuevo."
        ),
        herramienta=herramienta_usada,
    )
