# Pruebas del RAG sin llamar a la API: los embeddings se simulan.
import numpy as np
import openai
import pytest

import rag


@pytest.fixture
def chunks():
    return rag.cargar_chunks()


def indice_de(chunks, seccion):
    return next(i for i, c in enumerate(chunks) if c["fuente"].endswith(seccion))


def test_chunking_por_seccion_con_titulo_del_documento(chunks):
    assert len(chunks) == 10
    aprobacion = chunks[indice_de(chunks, "Aprobación")]
    assert aprobacion["fuente"] == "politica_despacho_extraordinario.md § Aprobación"
    assert aprobacion["texto"].startswith("Política de despacho extraordinario — Aprobación.")


def test_responde_con_fuente_cuando_la_pregunta_coincide(chunks, monkeypatch):
    vectores = np.eye(len(chunks))  # un vector distinto por chunk
    i = indice_de(chunks, "Aprobación")
    monkeypatch.setattr(rag, "embeber", lambda textos: vectores[[i]])  # la pregunta "es" ese chunk
    r = rag.responder("¿Quién autoriza un envío urgente?", chunks, vectores)
    assert r["encontrado"] is True
    assert r["metodo"] == "embeddings"
    assert r["fuente"].endswith("§ Aprobación")


def test_no_usa_rag_si_la_pregunta_no_es_de_politicas(chunks, monkeypatch):
    vectores = np.eye(len(chunks))
    pregunta_lejana = np.full((1, len(chunks)), 0.1)  # similitud baja con todos (< 0.45)
    monkeypatch.setattr(rag, "embeber", lambda textos: pregunta_lejana)
    r = rag.responder("¿Cuántas entregas tardías tuvo C-1002?", chunks, vectores)
    assert r["encontrado"] is False


def test_respaldo_tfidf_si_la_api_falla(chunks, monkeypatch):
    def api_caida(textos):
        raise openai.APIConnectionError(request=None)

    monkeypatch.setattr(rag, "embeber", api_caida)
    r = rag.responder("¿Despachan los sábados?", chunks, np.eye(len(chunks)))
    assert r["metodo"] == "tfidf (respaldo)"
    assert r["fuente"].endswith("§ Días y horario de despacho")
