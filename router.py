# router.py
# Router híbrido (D8): reglas para lo obvio, LLM para el resto y CLARIFY si hay duda.
import re
from datetime import date
from typing import Literal, Optional

import openai
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from config_caso import FECHA_REFERENCIA

load_dotenv()  # lee .env y carga OPENAI_API_KEY

MODELO_ROUTER = "gpt-6-luna"
PRECIO_ENTRADA, PRECIO_SALIDA = 0.10, 0.50  # USD por millón de tokens (gpt-6-luna)
CONFIANZA_MINIMA = 0.7

PATRON_CLIENTE = re.compile(r"\bC-\d{4}\b")
PATRON_SALUDO = re.compile(r"^\s*(hola|buenos días|buenas tardes|buenas noches|buenas)\b")
PALABRAS_SQL = ("entregas tardías", "historial", "hemos vendido", "cumplimiento")
PALABRAS_RAG = ("política", "politica")

INSTRUCCIONES = f"""Eres el router de AndesSupply, empresa B2B de logística. Clasifica la solicitud en UN destino:
- RAG: preguntas sobre políticas o procedimientos documentados (despachos, aprobaciones, plazos estándar).
- SQL: preguntas sobre el historial (ventas pasadas, entregas tardías, cumplimiento).
- TOOLS: pedidos o consultas del estado actual (stock, capacidad, fecha de entrega de un pedido concreto).
  Si piden "lo antes posible" o "cuanto antes" sin fecha, es TOOLS con fecha null: el sistema propondrá la más cercana.
- CLARIFY: falta producto o cantidad, la fecha es imprecisa (un día sin mes, "la próxima semana", "pronto")
  o la solicitud es ambigua.
- DIRECT: saludos o preguntas generales que no requieren datos.
Extrae cliente_id (formato C-####), sku, cantidad y fecha (AAAA-MM-DD). Hoy es lunes {FECHA_REFERENCIA}:
convierte las fechas relativas a partir de hoy. Si un dato no aparece, usa null; nunca lo inventes.
confianza: de 0 a 1, qué tan seguro estás del destino."""


class Decision(BaseModel):
    """Formato obligatorio de la respuesta del LLM (structured output)."""
    destino: Literal["RAG", "SQL", "TOOLS", "CLARIFY", "DIRECT"]
    confianza: float
    cliente_id: Optional[str]
    sku: Optional[str]
    cantidad: Optional[int]
    fecha: Optional[str]
    motivo: str


def resultado(destino, origen, confianza, motivo, cliente_id=None, sku=None, cantidad=None, fecha=None):
    """Formato único de salida del router, venga de una regla o del LLM."""
    return {"destino": destino, "origen": origen, "confianza": confianza, "motivo": motivo,
            "cliente_id": cliente_id, "sku": sku, "cantidad": cantidad, "fecha": fecha}


def aplicar_reglas(solicitud):
    """Reglas deterministas para los casos obvios. Devuelve None si ninguna aplica."""
    texto = solicitud.lower()
    cliente = PATRON_CLIENTE.search(solicitud)
    cliente_id = cliente.group() if cliente else None
    if PATRON_SALUDO.match(texto) and not re.search(r"\d", texto):
        return resultado("DIRECT", "regla", 1.0, "saludo sin datos")
    if any(p in texto for p in PALABRAS_SQL):
        return resultado("SQL", "regla", 1.0, "palabra clave de historial", cliente_id=cliente_id)
    if any(p in texto for p in PALABRAS_RAG):
        return resultado("RAG", "regla", 1.0, "menciona una política")
    return None


def clasificar_con_llm(solicitud):
    """Pide al LLM destino + datos en un formato fijo (Decision) e informa el costo."""
    cliente = OpenAI()
    respuesta = cliente.responses.parse(
        model=MODELO_ROUTER,
        instructions=INSTRUCCIONES,
        input=solicitud,
        text_format=Decision,
        reasoning={"effort": "none"},
    )
    uso = respuesta.usage
    costo = (uso.input_tokens * PRECIO_ENTRADA + uso.output_tokens * PRECIO_SALIDA) / 1_000_000
    print(f"  [costo] {uso.input_tokens}+{uso.output_tokens} tokens ≈ {costo:.6f} USD")
    return respuesta.output_parsed


def validar(decision):
    """No se confía a ciegas en el LLM (§13): se validan confianza y datos."""
    d = resultado(decision.destino, "llm", decision.confianza, decision.motivo,
                  decision.cliente_id, decision.sku, decision.cantidad, decision.fecha)
    if d["cliente_id"] and not PATRON_CLIENTE.fullmatch(d["cliente_id"]):
        d["cliente_id"] = None
    if d["fecha"]:
        try:
            date.fromisoformat(d["fecha"])
        except ValueError:
            d["fecha"] = None
    if d["confianza"] < CONFIANZA_MINIMA:
        d["motivo"] = f"confianza baja ({d['confianza']}) para {d['destino']}: {d['motivo']}"
        d["destino"] = "CLARIFY"
    elif d["destino"] == "TOOLS" and not (d["cliente_id"] or d["sku"]):
        d["motivo"] = "TOOLS sin cliente ni SKU"
        d["destino"] = "CLARIFY"
    return d


def enrutar(solicitud):
    """Punto de entrada: reglas primero; si no aplican, LLM validado; si el LLM falla, CLARIFY."""
    por_regla = aplicar_reglas(solicitud)
    if por_regla:
        return por_regla
    try:
        return validar(clasificar_con_llm(solicitud))
    except openai.OpenAIError as error:
        return resultado("CLARIFY", "respaldo", 0.0, f"LLM no disponible ({type(error).__name__})")