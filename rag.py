# rag.py
# RAG sobre las políticas de AndesSupply: chunking + búsqueda + respuesta con fuente.
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

POLITICAS_DIR = Path(__file__).parent / "data" / "politicas"
UMBRAL_TFIDF = 0.15  # por debajo, se considera que las políticas no responden
load_dotenv()  # lee .env y carga OPENAI_API_KEY
MODELO_EMBEDDINGS = "text-embedding-3-small"


def cargar_chunks():
    """Corta cada política en chunks: uno por sección '## '."""
    chunks = []
    for archivo in sorted(POLITICAS_DIR.glob("*.md")):
        texto = archivo.read_text(encoding="utf-8")
        for seccion in texto.split("\n## ")[1:]:  # [1:] salta el título '# ...' del documento
            titulo, _, contenido = seccion.partition("\n")
            chunks.append({
                "fuente": f"{archivo.name} § {titulo.strip()}",
                "texto": f"{titulo.strip()}. {contenido.strip()}",
            })
    return chunks


def buscar_tfidf(pregunta, chunks, k=2):
    """Devuelve los k chunks con más palabras importantes en común con la pregunta."""
    vectorizador = TfidfVectorizer(strip_accents="unicode", lowercase=True)
    matriz = vectorizador.fit_transform([c["texto"] for c in chunks])
    consulta = vectorizador.transform([pregunta])
    puntajes = cosine_similarity(consulta, matriz)[0]
    ranking = sorted(zip(puntajes, chunks), key=lambda par: par[0], reverse=True)
    return [{"puntaje": round(float(p), 3), **c} for p, c in ranking[:k]]


def responder(pregunta, chunks):
    """Respuesta con fuente, o aviso si las políticas no cubren la pregunta."""
    mejor = buscar_tfidf(pregunta, chunks, k=1)[0]
    if mejor["puntaje"] < UMBRAL_TFIDF:
        return {"encontrado": False, "puntaje": mejor["puntaje"],
                "respuesta": "Las políticas no cubren esta pregunta."}
    return {"encontrado": True, "puntaje": mejor["puntaje"],
            "respuesta": mejor["texto"], "fuente": mejor["fuente"]}

def embeber(textos):
    """Convierte una lista de textos en vectores de significado (1 llamada a la API)."""
    cliente = OpenAI()  # usa OPENAI_API_KEY del entorno
    respuesta = cliente.embeddings.create(model=MODELO_EMBEDDINGS, input=textos)
    return np.array([dato.embedding for dato in respuesta.data])


def buscar_embeddings(pregunta, chunks, vectores_chunks, k=2):
    """Devuelve los k chunks cuyo significado está más cerca del de la pregunta."""
    vector_pregunta = embeber([pregunta])
    puntajes = cosine_similarity(vector_pregunta, vectores_chunks)[0]
    ranking = sorted(zip(puntajes, chunks), key=lambda par: par[0], reverse=True)
    return [{"puntaje": round(float(p), 3), **c} for p, c in ranking[:k]]


if __name__ == "__main__":
    chunks = cargar_chunks()
    vectores_chunks = embeber([c["texto"] for c in chunks])  # 1 sola llamada para los 10 chunks
    print(f"{len(chunks)} chunks · vectores de {vectores_chunks.shape[1]} dimensiones")

    preguntas = [
        "¿Cuál es la política para un despacho extraordinario?",
        "¿Quién debe aprobar un despacho extraordinario?",
        "¿Despachan los sábados?",
        "¿Quién autoriza un envío urgente?",
        "¿Cuántas entregas tardías tuvo C-1002?",
    ]
    for pregunta in preguntas:
        tf = buscar_tfidf(pregunta, chunks, k=1)[0]
        em = buscar_embeddings(pregunta, chunks, vectores_chunks, k=1)[0]
        print(f"\n> {pregunta}")
        print(f"  TF-IDF     {tf['puntaje']:.3f} · {tf['fuente']}")
        print(f"  Embeddings {em['puntaje']:.3f} · {em['fuente']}")
