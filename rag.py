# rag.py
# RAG sobre las políticas de AndesSupply: chunking + búsqueda + respuesta con fuente.
# Búsqueda principal por embeddings (OpenAI); TF-IDF como respaldo si la API falla (D6).
import json
from pathlib import Path

import numpy as np
import openai
from dotenv import load_dotenv
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()  # lee .env y carga OPENAI_API_KEY

POLITICAS_DIR = Path(__file__).parent / "data" / "politicas"
CACHE_PATH = Path(__file__).parent / "data" / "cache_embeddings.json"
MODELO_EMBEDDINGS = "text-embedding-3-small"
PRECIO_USD_POR_MILLON = 0.02  # text-embedding-3-small
UMBRAL_EMBEDDINGS = 0.45  # calibrado con las Evidencias 8 y 9
UMBRAL_TFIDF = 0.15


def cargar_chunks():
    """Corta cada política en chunks (uno por sección '## ') con el título del documento (D7)."""
    chunks = []
    for archivo in sorted(POLITICAS_DIR.glob("*.md")):
        texto = archivo.read_text(encoding="utf-8")
        titulo_doc = texto.splitlines()[0].lstrip("# ").split(" · ")[0]
        for seccion in texto.split("\n## ")[1:]:  # [1:] salta el título '# ...' del documento
            titulo, _, contenido = seccion.partition("\n")
            chunks.append({
                "fuente": f"{archivo.name} § {titulo.strip()}",
                "texto": f"{titulo_doc} — {titulo.strip()}. {contenido.strip()}",
            })
    return chunks


def embeber(textos):
    """Convierte textos en vectores de significado (1 llamada a la API) e informa el costo."""
    cliente = OpenAI()  # usa OPENAI_API_KEY del entorno
    respuesta = cliente.embeddings.create(model=MODELO_EMBEDDINGS, input=textos)
    tokens = respuesta.usage.total_tokens
    print(f"  [costo] {tokens} tokens ≈ {tokens * PRECIO_USD_POR_MILLON / 1_000_000:.6f} USD")
    return np.array([dato.embedding for dato in respuesta.data])


def vectores_de_chunks(chunks):
    """Vectores de los chunks: los reutiliza de la caché si las políticas no cambiaron."""
    textos = [c["texto"] for c in chunks]
    if CACHE_PATH.exists():
        cache = json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        if cache["modelo"] == MODELO_EMBEDDINGS and cache["textos"] == textos:
            print("  [caché] vectores de los chunks reutilizados (0 USD)")
            return np.array(cache["vectores"])
    vectores = embeber(textos)
    CACHE_PATH.write_text(json.dumps({
        "modelo": MODELO_EMBEDDINGS, "textos": textos, "vectores": vectores.tolist(),
    }), encoding="utf-8")
    return vectores


def buscar_tfidf(pregunta, chunks, k=2):
    """Devuelve los k chunks con más palabras importantes en común con la pregunta."""
    vectorizador = TfidfVectorizer(strip_accents="unicode", lowercase=True)
    matriz = vectorizador.fit_transform([c["texto"] for c in chunks])
    consulta = vectorizador.transform([pregunta])
    puntajes = cosine_similarity(consulta, matriz)[0]
    ranking = sorted(zip(puntajes, chunks), key=lambda par: par[0], reverse=True)
    return [{"puntaje": round(float(p), 3), **c} for p, c in ranking[:k]]


def buscar_embeddings(pregunta, chunks, vectores_chunks, k=2):
    """Devuelve los k chunks cuyo significado está más cerca del de la pregunta."""
    vector_pregunta = embeber([pregunta])
    puntajes = cosine_similarity(vector_pregunta, vectores_chunks)[0]
    ranking = sorted(zip(puntajes, chunks), key=lambda par: par[0], reverse=True)
    return [{"puntaje": round(float(p), 3), **c} for p, c in ranking[:k]]


def responder(pregunta, chunks, vectores_chunks=None):
    """Respuesta con fuente usando embeddings; si la API falla, usa TF-IDF como respaldo."""
    try:
        if vectores_chunks is None:
            raise openai.OpenAIError("sin vectores de chunks")
        mejor = buscar_embeddings(pregunta, chunks, vectores_chunks, k=1)[0]
        metodo, umbral = "embeddings", UMBRAL_EMBEDDINGS
    except openai.OpenAIError as error:
        print(f"  [respaldo] embeddings no disponibles ({type(error).__name__}); uso TF-IDF")
        mejor = buscar_tfidf(pregunta, chunks, k=1)[0]
        metodo, umbral = "tfidf (respaldo)", UMBRAL_TFIDF

    if mejor["puntaje"] < umbral:
        return {"encontrado": False, "metodo": metodo, "puntaje": mejor["puntaje"],
                "respuesta": "Las políticas no cubren esta pregunta."}
    return {"encontrado": True, "metodo": metodo, "puntaje": mejor["puntaje"],
            "respuesta": mejor["texto"], "fuente": mejor["fuente"]}


if __name__ == "__main__":
    chunks = cargar_chunks()
    try:
        vectores_chunks = vectores_de_chunks(chunks)
    except openai.OpenAIError as error:
        print(f"  [respaldo] no se pudieron calcular los vectores ({type(error).__name__})")
        vectores_chunks = None

    preguntas = [
        "¿Cuál es la política para un despacho extraordinario?",
        "¿Quién debe aprobar un despacho extraordinario?",
        "¿Despachan los sábados?",
        "¿Quién autoriza un envío urgente?",
        "¿Cuántas entregas tardías tuvo C-1002?",
    ]
    for pregunta in preguntas:
        print(f"\n> {pregunta}")
        r = responder(pregunta, chunks, vectores_chunks)
        print(f"  {r['metodo']} · puntaje={r['puntaje']} · {r.get('fuente', 'sin fuente')}")
        print(f"  {r['respuesta'][:110]}")