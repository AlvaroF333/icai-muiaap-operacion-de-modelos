from fastapi import APIRouter, Depends

from app.schemas.chat import ChatEntrada, ChatSalida
from app.services.llm import get_llm
from app.services.orquestador import responder

router = APIRouter()


@router.post("/chat", response_model=ChatSalida)
def chat(entrada: ChatEntrada, llm=Depends(get_llm)) -> ChatSalida:
    """Conversación -> respuesta del asistente. El LLM llega por Depends para que los
    tests puedan sustituirlo (app.dependency_overrides[get_llm])."""
    return responder(entrada.mensajes, llm)
