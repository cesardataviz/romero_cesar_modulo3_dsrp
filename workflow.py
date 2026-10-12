# workflow.py
# Workflow con estado (LangGraph). Conecta router, Tools, Reglas, RAG y SQL.
# Hito 4: checkpoint persistente (SQLite) + interrupt() para que el Supervisor de logística
# apruebe o rechace las excepciones, reanudando con el mismo id_hilo.
import sqlite3
import sys
from datetime import date
from pathlib import Path
from typing import TypedDict

import openai
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, RetryPolicy, interrupt

import rag
import router
from config_caso import CASO_ID, SEMILLA, costo_extraordinario
from consultas_sql import cumplimiento_entregas, entregas_tardias
from reglas import evaluar_pedido, fecha_despacho, fecha_minima_entrega, sumar_dias_habiles
from router import enrutar, es_fallo_transitorio
from tools import consultar_capacidad, consultar_cliente, consultar_stock, consultar_transito

CHECKPOINT_PATH = Path(__file__).parent / "data" / "checkpoints.db"

# Retry SOLO para la dependencia transitoria (la API del LLM en el nodo enrutar).
# Las reglas de negocio y los datos inválidos nunca se reintentan.
REINTENTO_LLM = RetryPolicy(max_attempts=3, initial_interval=0.5, retry_on=es_fallo_transitorio)


class Estado(TypedDict, total=False):
    solicitud: str          # texto original del cliente
    destino: str            # RAG / SQL / TOOLS / CLARIFY / DIRECT
    cliente_id: str
    sku: str
    cantidad: int
    fecha: str              # AAAA-MM-DD
    dias_transito: int
    stock: int              # foto del momento: se vuelve a consultar al reanudar
    libres: int             # capacidad libre el día de despacho
    decision: str           # APROBADO / EXCEPCION / RECHAZADO / DATOS_INVALIDOS / APROBADO_EXTRAORDINARIO
    motivos: list[str]
    aprobacion: str         # "aprobar" / "rechazar" (lo decide el supervisor)
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


def nodo_supervisor(estado):
    """⑦ HITL: pausa el flujo hasta que el Supervisor de logística apruebe o rechace.

    Al reanudar, LangGraph vuelve a ejecutar este nodo desde la primera línea:
    por eso NO hay side effects (correos, reservas) antes de interrupt().
    """
    respuesta = interrupt({
        "pregunta": "¿Autorizas el despacho extraordinario?",
        "pedido": f"{estado['cantidad']} {estado['sku']} para {estado['cliente_id']} el {estado['fecha']}",
        "motivos": estado["motivos"],
        "costo_usd": costo_extraordinario,
    })
    respuesta = str(respuesta).strip().lower()
    if respuesta not in ("aprobar", "rechazar"):
        respuesta = "rechazar"  # una respuesta no válida nunca autoriza un gasto
    return {"aprobacion": respuesta}


def nodo_reverificar(estado):
    """⑧ Tras la aprobación, vuelve a consultar el stock: pudo cambiar mientras el flujo estaba pausado (D10)."""
    stock = consultar_stock(estado["sku"])["stock_disponible"]
    if estado["cantidad"] > stock:
        return {"stock": stock, "decision": "RECHAZADO",
                "motivos": [f"Al reanudar, el stock bajó: pide {estado['cantidad']}, hay {stock}"]}
    return {"stock": stock, "decision": "APROBADO_EXTRAORDINARIO"}


def fecha_estandar_con_capacidad(estado):
    """Primera fecha estándar (desde la mínima) cuyo día de despacho tiene capacidad para el pedido."""
    fecha = fecha_minima_entrega(estado["dias_transito"])
    for _ in range(20):  # busca hasta 20 días hábiles hacia adelante
        despacho = fecha_despacho(fecha, estado["dias_transito"])
        if consultar_capacidad(despacho.isoformat())["libres"] >= estado["cantidad"]:
            return fecha.isoformat()
        fecha = sumar_dias_habiles(fecha, 1)
    return None


def nodo_responder(estado):
    """⑤ Arma el mensaje final del flujo de pedido según la decisión."""
    motivos = "; ".join(estado.get("motivos", []))
    pedido = f"{estado.get('cantidad')} {estado.get('sku')} para {estado.get('cliente_id')}"
    decision = estado["decision"]
    if decision == "APROBADO":
        texto = f"Confirmado: {pedido}, entrega el {estado['fecha']}."
    elif decision == "APROBADO_EXTRAORDINARIO":
        texto = (f"Confirmado con despacho extraordinario autorizado por el Supervisor de logística "
                 f"({costo_extraordinario} USD): {pedido}, entrega el {estado['fecha']}.")
    elif decision == "EXCEPCION":  # solo llega aquí si el supervisor rechazó
        alternativa = fecha_estandar_con_capacidad(estado)
        texto = (f"El Supervisor de logística no autorizó el despacho extraordinario para {pedido} "
                 f"el {estado['fecha']}. Fecha estándar más cercana con capacidad: {alternativa or 'sin cupo próximo'}.")
    elif decision == "RECHAZADO":
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


def ruta_tras_evaluar(estado):
    return "supervisor" if estado["decision"] == "EXCEPCION" else "responder"


def ruta_tras_supervisor(estado):
    return "reverificar" if estado["aprobacion"] == "aprobar" else "responder"


# ---------- Construcción del grafo ----------

def construir_workflow(checkpointer=None):
    grafo = StateGraph(Estado)
    grafo.add_node("enrutar", nodo_enrutar, retry_policy=REINTENTO_LLM)
    grafo.add_node("validar_datos", nodo_validar_datos)
    grafo.add_node("consultar_estado", nodo_consultar_estado)
    grafo.add_node("evaluar", nodo_evaluar)
    grafo.add_node("supervisor", nodo_supervisor)
    grafo.add_node("reverificar", nodo_reverificar)
    grafo.add_node("responder", nodo_responder)
    grafo.add_node("atender_consulta", nodo_atender_consulta)

    grafo.add_edge(START, "enrutar")
    grafo.add_conditional_edges("enrutar", ruta_tras_enrutar, ["validar_datos", "atender_consulta"])
    grafo.add_conditional_edges("validar_datos", ruta_tras_validar, ["consultar_estado", "responder"])
    grafo.add_edge("consultar_estado", "evaluar")
    grafo.add_conditional_edges("evaluar", ruta_tras_evaluar, ["supervisor", "responder"])
    grafo.add_conditional_edges("supervisor", ruta_tras_supervisor, ["reverificar", "responder"])
    grafo.add_edge("reverificar", "responder")
    grafo.add_edge("responder", END)
    grafo.add_edge("atender_consulta", END)
    return grafo.compile(checkpointer=checkpointer)


def abrir_workflow():
    """Workflow con checkpoint persistente: el State de cada id_hilo se guarda en data/checkpoints.db."""
    conexion = sqlite3.connect(CHECKPOINT_PATH, check_same_thread=False)
    return construir_workflow(SqliteSaver(conexion))


def guardar_diagrama(app):
    """Guarda el diagrama del grafo (Mermaid) generado por LangGraph en docs/."""
    ruta = Path(__file__).parent / "docs" / "diagrama_workflow.md"
    mermaid = app.get_graph().draw_mermaid()
    contenido = f"# Diagrama del workflow (generado por LangGraph)\n\n```mermaid\n{mermaid}```\n"
    ruta.write_text(contenido, encoding="utf-8")
    print(f"Diagrama guardado en {ruta.name}")


# ---------- Ejecución ----------

def mostrar_pasos(app, entrada, config):
    """Ejecuta (o reanuda) el flujo mostrando cada nodo y lo que escribe en el State."""
    for paso in app.stream(entrada, config, stream_mode="updates"):
        for nodo, cambios in paso.items():
            if nodo == "__interrupt__":
                datos = cambios[0].value
                print(f"\n  [PAUSA] Flujo pausado · id_hilo={config['configurable']['thread_id']}")
                print(f"          {datos['pregunta']} {datos['pedido']} · costo {datos['costo_usd']} USD")
                print(f"          Motivos: {'; '.join(datos['motivos'])}")
                print(f"          Para continuar: uv run workflow.py reanudar "
                      f"{config['configurable']['thread_id']} aprobar|rechazar")
            else:
                print(f"  [{nodo}] {cambios}")
    estado = app.get_state(config)
    if not estado.next:
        print(f"  → {estado.values.get('respuesta')}")


def iniciar(app, id_hilo, solicitud):
    config = {"configurable": {"thread_id": id_hilo}}
    if app.get_state(config).values:
        print(f"Ya existe un flujo con id_hilo={id_hilo}. Usa otro id_hilo.")
        return
    print(f"=== [{id_hilo}] {solicitud}")
    try:
        mostrar_pasos(app, {"solicitud": solicitud}, config)
    except openai.OpenAIError as error:
        print(f"  [ERROR] Fallo técnico persistente tras {REINTENTO_LLM.max_attempts} intentos "
              f"({type(error).__name__}). Intenta más tarde.")


def reanudar(app, id_hilo, decision_supervisor):
    config = {"configurable": {"thread_id": id_hilo}}
    estado = app.get_state(config)
    if not estado.values:
        print(f"No existe ningún flujo con id_hilo={id_hilo}: no hay nada que reanudar.")
        return
    if "supervisor" not in estado.next:
        print(f"El flujo {id_hilo} no está esperando al supervisor (siguiente paso: {estado.next or 'terminado'}).")
        return
    print(f"=== Reanudando [{id_hilo}] con decisión del supervisor: {decision_supervisor}")
    mostrar_pasos(app, Command(resume=decision_supervisor), config)


def ver_estado(app, id_hilo):
    estado = app.get_state({"configurable": {"thread_id": id_hilo}})
    if not estado.values:
        print(f"No existe ningún flujo con id_hilo={id_hilo}.")
        return
    print(f"id_hilo={id_hilo} · siguiente paso: {estado.next or 'terminado'}")
    for campo, valor in estado.values.items():
        print(f"  {campo}: {valor}")


USO = """Uso:
  uv run workflow.py iniciar <id_hilo> "<solicitud>" [--fallos N]   (N: fallos de conexión simulados)
  uv run workflow.py reanudar <id_hilo> aprobar|rechazar
  uv run workflow.py estado <id_hilo>
  uv run workflow.py diagrama"""

if __name__ == "__main__":
    print(f"{CASO_ID} · semilla {SEMILLA}")
    app = abrir_workflow()
    argumentos = sys.argv[1:]
    if "--fallos" in argumentos:
        i = argumentos.index("--fallos")
        router.SIMULAR_FALLOS = int(argumentos[i + 1])
        del argumentos[i:i + 2]
    if len(argumentos) == 3 and argumentos[0] == "iniciar":
        iniciar(app, argumentos[1], argumentos[2])
    elif len(argumentos) == 3 and argumentos[0] == "reanudar":
        reanudar(app, argumentos[1], argumentos[2])
    elif len(argumentos) == 2 and argumentos[0] == "estado":
        ver_estado(app, argumentos[1])
    elif argumentos == ["diagrama"]:
        guardar_diagrama(app)
    else:
        print(USO)
