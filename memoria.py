"""Chroma local. El mismo embedding indexa y consulta."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import chromadb
from chromadb.utils import embedding_functions

COLLECTION = "conocimiento"
TOP_K = 4

_embedding = None


def persist_path(explicit: Path | None = None) -> Path:
    if explicit is not None:
        return explicit
    return Path(os.environ.get("VECTORSTORE_PATH", "./vectorstore"))


def embedding_function():
    """DefaultEmbeddingFunction de Chroma. No se mezcla con otro proveedor."""
    global _embedding
    if _embedding is None:
        _embedding = embedding_functions.DefaultEmbeddingFunction()
    return _embedding


def abrir(path: Path | None = None):
    destino = persist_path(path)
    destino.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(destino))
    return client.get_or_create_collection(
        name=COLLECTION,
        embedding_function=embedding_function(),
    )


def vaciar(path: Path | None = None) -> None:
    destino = persist_path(path)
    if not destino.exists():
        return
    client = chromadb.PersistentClient(path=str(destino))
    nombres = [item.name for item in client.list_collections()]
    if COLLECTION in nombres:
        client.delete_collection(COLLECTION)


def buscar(consulta: str, k: int = TOP_K, path: Path | None = None) -> list[dict[str, Any]]:
    coleccion = abrir(path)
    if coleccion.count() == 0:
        return []
    encontrado = coleccion.query(query_texts=[consulta], n_results=min(k, coleccion.count()))
    documentos = (encontrado.get("documents") or [[]])[0]
    metadatos = (encontrado.get("metadatas") or [[]])[0]
    distancias = (encontrado.get("distances") or [[]])[0]
    return [
        {
            "texto": documento,
            "fuente": (metadato or {}).get("fuente", ""),
            "chunk": (metadato or {}).get("chunk", 0),
            "distancia": distancia,
        }
        for documento, metadato, distancia in zip(documentos, metadatos, distancias)
    ]
