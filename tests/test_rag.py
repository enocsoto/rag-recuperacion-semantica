"""Ingesta, chunking y recuperación. No llama al LLM."""

from __future__ import annotations

import unittest
from pathlib import Path

from ingesta import CHUNK_OVERLAP, CHUNK_SIZE, cargar, fragmentar, limpiar, tokens_de
from memoria import buscar
from rag import NO_LO_SE, RespuestaRAG, prompt

DATA = Path(__file__).resolve().parents[1] / "data"


class TestLimpiezaYChunks(unittest.TestCase):
    def test_limpia_encabezado_y_basura(self) -> None:
        sucio = "ACME — Manual — Pág. 2\nPolítica■■\ntexto    doble"
        limpio = limpiar(sucio)
        self.assertNotIn("Pág.", limpio)
        self.assertNotIn("■", limpio)
        self.assertIn("texto doble", limpio)

    def test_chunk_respeta_tokens_y_overlap(self) -> None:
        oracion = "El turno revisa el tablero norte y anota el incidente del backup. "
        piezas = fragmentar("sintetico.md", oracion * 80)
        self.assertGreaterEqual(len(piezas), 2)
        for pieza in piezas:
            self.assertLessEqual(tokens_de(str(pieza["texto"])), CHUNK_SIZE)
        cola = str(piezas[0]["texto"]).split()[-6:]
        siguiente = str(piezas[1]["texto"])
        self.assertTrue(any(palabra in siguiente for palabra in cola if len(palabra) > 4))
        self.assertEqual(CHUNK_OVERLAP, 50)


class TestIngesta(unittest.TestCase):
    def test_no_reindexa_y_recupera_el_snapshot(self) -> None:
        destino = Path(self.id().replace(".", "_"))
        destino = Path("/tmp") / destino.name
        primero = cargar(DATA, destino, force=True)
        segundo = cargar(DATA, destino, force=False)
        self.assertGreater(primero, 0)
        self.assertEqual(primero, segundo)
        hits = buscar("hora del snapshot diario de la base de pedidos", path=destino)
        self.assertTrue(hits)
        self.assertEqual(hits[0]["fuente"], "respaldos.md")
        self.assertIn("02:10", hits[0]["texto"])


class TestContrato(unittest.TestCase):
    def test_prompt_obliga_a_decir_no_lo_se(self) -> None:
        texto = str(prompt)
        self.assertIn(NO_LO_SE, texto)
        self.assertIn("contexto", prompt.input_variables)
        self.assertIn("pregunta", prompt.input_variables)

    def test_esquema_tiene_respuesta_y_referencias(self) -> None:
        modelo = RespuestaRAG(respuesta=NO_LO_SE, referencias=[])
        self.assertEqual(modelo.referencias, [])
        self.assertIn("respuesta", RespuestaRAG.model_fields)
        self.assertIn("referencias", RespuestaRAG.model_fields)


if __name__ == "__main__":
    unittest.main()
