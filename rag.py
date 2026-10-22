"""Cadena RAG asíncrona. Responde solo con los fragmentos recuperados."""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from memoria import TOP_K, buscar

logger = logging.getLogger(__name__)

NO_LO_SE = "No lo sé"


class RespuestaRAG(BaseModel):
    """Salida estructurada: texto y fuentes."""

    respuesta: str = Field(description="Respuesta basada solo en el contexto, o 'No lo sé'.")
    referencias: list[str] = Field(
        description="Nombres de archivo usados. Lista vacía si la respuesta es 'No lo sé'."
    )


parser = PydanticOutputParser(pydantic_object=RespuestaRAG)

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Eres un asistente técnico de la plataforma Norte. "
            "Responde solo con el CONTEXTO. No uses conocimiento externo. "
            "Si la respuesta no está en el contexto, la respuesta es exactamente "
            f"'{NO_LO_SE}' y referencias queda vacía. "
            "Si sí está, cita en referencias solo los nombres de archivo del contexto.\n"
            "{format_instructions}",
        ),
        ("human", "CONTEXTO:\n{contexto}\n\nPREGUNTA:\n{pregunta}"),
    ]
).partial(format_instructions=parser.get_format_instructions())


def chat_model() -> ChatOpenAI | ChatAnthropic:
    """LLM según LLM_PROVIDER. Los embeddings no pasan por este cliente."""
    load_dotenv()
    proveedor = os.environ.get("LLM_PROVIDER", "openai").strip().lower() or "openai"
    if proveedor == "openai":
        if not os.environ.get("OPENAI_API_KEY", "").strip():
            raise RuntimeError("Falta OPENAI_API_KEY para el proveedor openai.")
        return ChatOpenAI(model="gpt-4o-mini", temperature=0, max_retries=0)
    if proveedor == "anthropic":
        if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
            raise RuntimeError("Falta ANTHROPIC_API_KEY para el proveedor anthropic.")
        return ChatAnthropic(model="claude-3-5-haiku-latest", temperature=0, max_retries=0)
    raise RuntimeError(f"LLM_PROVIDER no reconocido: {proveedor}")


def formatear(fragmentos: list[dict]) -> str:
    if not fragmentos:
        return "(sin fragmentos)"
    bloques = []
    for pieza in fragmentos:
        bloques.append(f"[fuente: {pieza['fuente']} | chunk {pieza['chunk']}]\n{pieza['texto']}")
    return "\n\n".join(bloques)


def preparar(pregunta: str, path: Path | None = None) -> dict[str, str]:
    fragmentos = buscar(pregunta, k=TOP_K, path=path)
    logger.info("recuperados: %s", [pieza["fuente"] for pieza in fragmentos])
    return {"contexto": formatear(fragmentos), "pregunta": pregunta}


def construir_cadena(path: Path | None = None):
    """LCEL: recuperación | prompt | modelo | parser."""
    modelo = chat_model()
    cadena = RunnableLambda(lambda pregunta: preparar(pregunta, path)) | prompt | modelo | parser
    return cadena.with_retry(
        retry_if_exception_type=(OutputParserException,),
        stop_after_attempt=2,
    )


async def get_rag_response(query: str, path: Path | None = None) -> RespuestaRAG:
    """Busca en Chroma, arma el prompt y llama al LLM de forma asíncrona."""
    logger.info("consulta: %s", query)
    respuesta = await construir_cadena(path).ainvoke(query)
    logger.info("respuesta: %s", respuesta.model_dump())
    return respuesta


async def _demo() -> None:
    logging.basicConfig(level=logging.INFO)
    dentro = await get_rag_response(
        "¿A qué hora UTC se toma el snapshot diario de la base de pedidos y cuántos días se retiene?"
    )
    trampa = await get_rag_response("¿Cuántos días de vacaciones tiene el equipo de plataforma Norte?")
    print(dentro.model_dump_json(indent=2))
    print(trampa.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(_demo())
