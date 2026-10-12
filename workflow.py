# workflow.py
# Hito 3: workflow con estado (LangGraph). Conecta router, Tools, Reglas, RAG y SQL.
from datetime import date
from pathlib import Path
from typing import TypedDict

import openai
from langgraph.graph import END, START, StateGraph

import rag
from config_caso import CASO_ID, SEMILLA, costo_extraordinario
from consultas_sql import cumplimiento_entregas, entregas_tardias
from reglas import evaluar_pedido, fecha_despacho, fecha_minima_entrega
from router import enrutar
from tools import consultar_capacidad, consultar_cliente, consultar_stock, consultar_transito


class Estado(TypedDict, total=False):
    solicitud: str          # texto original del cliente
    destino: str            # RAG / SQL / TOOLS / CLARIFY / DIRECT
    cliente_id: str
    sku: str
    cantidad: int
    fecha: str              # AAAA-MM-DD
    dias_transito: int
    stock: int              # foto del momento (re-verificar al reanudar, Hito 4)
    libres: int             # capacidad libre el día de despacho
    decision: str           # APROBADO / EXCEPCION / RECHAZADO / DATOS_INVALIDOS
    motivos: list[str]
    respuesta: str          # texto final para el usuario


# ---------- Nodos ----------

def nodo_enrutar(estado):
    """① Clasifica la solicitud y extrae los datos del pedido."""
    r = enrutar(estado["solicitud"])
    return {campo: r[campo] for campo in ("destino", "cliente_id", "sku", "cantidad", "fecha")}


def nodo_validar_datos(estado):
    """② Verifica cliente, SKU, cantidad y ciudad; si no hay fecha ("lo antes posible"), propone la mínima (D9)."""
    motivos = []
    cliente = consultar_cliente(estado["cliente_id"]) if estado.get("cliente_id") else None
    if not cliente:
        motivos.append("Falta el código del cliente (C-####)")
    elif not cliente["ok"]:
        motivos.append(cliente["motivo"])
    producto = consultar_stock(estado["sku"]) if estado.get("sku") else None
    if not producto:
        motivos.append("Falta el producto (SKU)")
    elif not producto["ok"]:
        motivos.append(producto["motivo"])
    if not estado.get("cantidad"):
        motivos.append("Falta la cantidad")
    transito = consultar_transito(cliente["ciudad"]) if cliente and cliente["ok"] else None
    if transito and not transito["ok"]:
        motivos.append(transito["motivo"])

    if motivos:
        return {"decision": "DATOS_INVALIDOS", "motivos": motivos}
    cambios = {"dias_transito": transito["dias_transito"]}
    if not estado.get("fecha"):
        cambios["fecha"] = fecha_minima_entrega(transito["dias_transito"]).isoformat()
    return cambios


def nodo_consultar_estado(estado):
    """③ Stock actual y capacidad libre del día en que debe salir el despacho."""
    despacho = fecha_despacho(date.fromisoformat(estado["fecha"]), estado["dias_transito"])
    stock = consultar_stock(estado["sku"])["stock_disponible"]
    libres = consultar_capacidad(despacho.isoformat())["libres"]
    return {"stock": stock, "libres": libres}


def nodo_evaluar(estado):
    """④ Aplica las reglas de negocio (Python puro, sin LLM)."""
    r = evaluar_pedido(estado["cantidad"], estado["fecha"], estado["stock"],
                       estado["libres"], estado["dias_transito"])
    return {"decision": r["decision"], "motivos": r["motivos"]}


def nodo_responder(estado):
    """⑤ Arma el mensaje final del flujo de pedido según la decisión."""
    motivos = "; ".join(estado.get("motivos", []))
    pedido = f"{estado.get('cantidad')} {estado.get('sku')} para {estado.get('cliente_id')}"
    if estado["decision"] == "APROBADO":
        texto = f"Confirmado: {pedido}, entrega el {estado['fecha']}."
    elif estado["decision"] == "EXCEPCION":
        texto = (f"No podemos confirmar {pedido} el {estado['fecha']} sin aprobación del Supervisor de logística "
                 f"(despacho extraordinario: {costo_extraordinario} USD). Motivos: {motivos}.")
    elif estado["decision"] == "RECHAZADO":
        texto = f"No podemos comprometer la entrega de {pedido}: {motivos}."
    else:
        texto = f"No pudimos procesar el pedido: {motivos}."
    return {"respuesta": texto}


def nodo_atender_consulta(estado):
    """⑥ Responde lo que no es un pedido: RAG, SQL, DIRECT o CLARIFY."""
    destino = estado["destino"]
    if destino == "RAG":
        chunks = rag.cargar_chunks()
        try:
            vectores = rag.vectores_de_chunks(chunks)
        except openai.OpenAIError:
            vectores = None
        r = rag.responder(estado["solicitud"], chunks, vectores)
        texto = f"{r['respuesta']} (Fuente: {r['fuente']})" if r["encontrado"] else r["respuesta"]
    elif destino == "SQL":
        cliente_id = estado.get("cliente_id")
        if not cliente_id or not consultar_cliente(cliente_id)["ok"]:
            texto = "Indica el código de un cliente registrado (C-####) para consultar su historial."
        else:
            c = cumplimiento_entregas(cliente_id)
            tardias = entregas_tardias(cliente_id)
            texto = (f"{cliente_id}: {c['a_tiempo'] or 0} de {c['total']} entregas a tiempo; "
                     f"{len(tardias)} entregas tardías.")
    elif destino == "DIRECT":
        texto = ("Hola, soy el asistente de despachos de AndesSupply. Puedo confirmar fechas de entrega, "
                 "consultar políticas de despacho y revisar el historial de entregas de un cliente.")
    else:
        texto = ("Necesito más información para ayudarte: indica cliente, producto, cantidad "
                 "y una fecha completa (por ejemplo, 'el jueves 15').")
    return {"respuesta": texto}


# ---------- Bifurcaciones (conditional edges) ----------

def ruta_tras_enrutar(estado):
    return "validar_datos" if estado["destino"] == "TOOLS" else "atender_consulta"


def ruta_tras_validar(estado):
    return "responder" if estado.get("decision") == "DATOS_INVALIDOS" else "consultar_estado"


# ---------- Construcción del grafo ----------

def construir_workflow():
    grafo = StateGraph(Estado)
    grafo.add_node("enrutar", nodo_enrutar)
    grafo.add_node("validar_datos", nodo_validar_datos)
    grafo.add_node("consultar_estado", nodo_consultar_estado)
    grafo.add_node("evaluar", nodo_evaluar)
    grafo.add_node("responder", nodo_responder)
    grafo.add_node("atender_consulta", nodo_atender_consulta)

    grafo.add_edge(START, "enrutar")
    grafo.add_conditional_edges("enrutar", ruta_tras_enrutar, ["validar_datos", "atender_consulta"])
    grafo.add_conditional_edges("validar_datos", ruta_tras_validar, ["consultar_estado", "responder"])
    grafo.add_edge("consultar_estado", "evaluar")
    grafo.add_edge("evaluar", "responder")
    grafo.add_edge("responder", END)
    grafo.add_edge("atender_consulta", END)
    return grafo.compile()


def guardar_diagrama(app):
    """Guarda el diagrama del grafo (Mermaid) generado por LangGraph en docs/."""
    ruta = Path(__file__).parent / "docs" / "diagrama_workflow.md"
    mermaid = app.get_graph().draw_mermaid()
    contenido = f"# Diagrama del workflow (generado por LangGraph)\n\n```mermaid\n{mermaid}```\n"
    ruta.write_text(contenido, encoding="utf-8")
    print(f"Diagrama guardado en {ruta.name}")


def ejecutar(app, solicitud):
    """Ejecuta una solicitud mostrando qué nodo se ejecuta y qué escribe en el State."""
    print(f"\n=== {solicitud}")
    final = {}
    for paso in app.stream({"solicitud": solicitud}, stream_mode="updates"):
        for nodo, cambios in paso.items():
            print(f"  [{nodo}] {cambios}")
            final.update(cambios)
    print(f"  → {final.get('respuesta')}")
    return final


if __name__ == "__main__":
    print(f"{CASO_ID} · semilla {SEMILLA}")
    app = construir_workflow()
    guardar_diagrama(app)
    for solicitud in [
        "Hola, ¿qué puedes hacer por mí?",                                # ruta directa
        "C-1003 necesita 12 EDGE-ORIN para el jueves 15 de octubre.",    # caso base → EXCEPCION
        "C-1004 necesita 5 PLC-S7M en Arequipa para el jueves 22 de octubre.",  # APROBADO
        "C-1099 quiere 10 SENS-PROX para el lunes 19 de octubre.",       # cliente inexistente
    ]:
        ejecutar(app, solicitud)
