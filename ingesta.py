"""Lee /data, parte por tokens y guarda en Chroma. No reindexa si ya hay datos."""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter

from memoria import COLLECTION, abrir, persist_path, vaciar

logger = logging.getLogger(__name__)

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
DATA_DIR = Path(__file__).with_name("data")

_tokenizer = tiktoken.get_encoding("cl100k_base")


def tokens_de(texto: str) -> int:
    return len(_tokenizer.encode(texto))


def limpiar(texto: str) -> str:
    """Quita encabezados de página, el carácter ■ y espacios de más."""
    sin_encabezado = re.sub(r"(?m)^[^\n]*Pág\.\s*\d+[^\n]*\n?", "", texto)
    sin_basura = sin_encabezado.replace("■", "")
    espacios = re.sub(r"[ \t]{2,}", " ", sin_basura)
    return re.sub(r"\n{3,}", "\n\n", espacios).strip()


def splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=tokens_de,
        separators=["\n\n", "\n", ". ", " ", ""],
        keep_separator="end",
    )


def leer_documentos(data_dir: Path) -> list[tuple[str, str]]:
    archivos = sorted([*data_dir.glob("*.md"), *data_dir.glob("*.txt")])
    return [(ruta.name, ruta.read_text(encoding="utf-8")) for ruta in archivos]


def fragmentar(nombre: str, texto: str) -> list[dict[str, str | int]]:
    piezas = splitter().split_text(limpiar(texto))
    fragmentos = []
    for indice, pieza in enumerate(piezas):
        logger.info("%s chunk %s: %s tokens", nombre, indice, tokens_de(pieza))
        fragmentos.append({"fuente": nombre, "chunk": indice, "texto": pieza})
    return fragmentos


def cargar(data_dir: Path, persist_path: Path, force: bool = False) -> int:
    """Indexa data_dir. Si la colección ya tiene vectores, no vuelve a embeber."""
    if force:
        vaciar(persist_path)
    coleccion = abrir(persist_path)
    if not force and coleccion.count() > 0:
        logger.info("La colección %s ya tiene %s chunks. No se reindexa.", COLLECTION, coleccion.count())
        return coleccion.count()

    ids: list[str] = []
    documentos: list[str] = []
    metadatos: list[dict[str, str | int]] = []
    for nombre, texto in leer_documentos(data_dir):
        for fragmento in fragmentar(nombre, texto):
            ids.append(f"{fragmento['fuente']}:{fragmento['chunk']}")
            documentos.append(str(fragmento["texto"]))
            metadatos.append({"fuente": str(fragmento["fuente"]), "chunk": int(fragmento["chunk"])})

    if ids:
        coleccion.upsert(ids=ids, documents=documentos, metadatas=metadatos)
    logger.info("Indexados %s chunks en %s", coleccion.count(), persist_path)
    return coleccion.count()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Ingesta de documentos en Chroma local.")
    parser.add_argument("--force", action="store_true", help="Borra la colección y vuelve a indexar.")
    args = parser.parse_args()
    total = cargar(DATA_DIR, persist_path(), force=args.force)
    print(f"Chunks en la colección: {total}")


if __name__ == "__main__":
    main()
