# app.py
# Interfaz web (Gradio) del agente de despachos de AndesSupply.
# Pestaña Cliente: conversa con el workflow. Pestaña Supervisor: revisa y decide las excepciones (HITL).
# Usa el mismo workflow, checkpoint y reglas que la terminal: la interfaz no agrega lógica de negocio.
import os
from datetime import datetime

import gradio as gr
import openai
from langgraph.types import Command

import workflow
from cargar_datos import DB_PATH, reconstruir_base
from config_caso import CASO_ID, SEMILLA, capacidad_diaria, costo_extraordinario, ventana_entrega_dias

if not DB_PATH.exists():
    reconstruir_base()
APP = workflow.abrir_workflow()

EJEMPLOS = [
    "C-1003 necesita 12 EDGE-ORIN para el jueves 15 de octubre.",
    "C-1004 necesita 5 PLC-S7M en Arequipa para el jueves 22 de octubre.",
    "¿Quién autoriza un envío urgente?",
    "¿Cuántas entregas tardías tuvo C-1002?",
]
COLUMNAS = ["Expediente", "Cliente", "Pedido", "Fecha", "Motivos"]


def config(id_hilo):
    return {"configurable": {"thread_id": id_hilo}}


# ---------- Pestaña Cliente ----------

def atender(mensaje, historial):
    """Cada mensaje abre un expediente nuevo (id_hilo) y recorre el workflow."""
    id_hilo = f"WEB-{datetime.now():%Y%m%d-%H%M%S-%f}"
    try:
        APP.invoke({"solicitud": mensaje}, config(id_hilo))
    except openai.OpenAIError as error:  # fallo técnico persistente tras los reintentos
        return f"El servicio no está disponible en este momento ({type(error).__name__}). Intenta más tarde."
    estado = APP.get_state(config(id_hilo))
    if "supervisor" in estado.next:
        return (f"Tu pedido requiere aprobación del Supervisor de logística "
                f"(despacho extraordinario: {costo_extraordinario} USD).\n\n"
                f"Expediente: **{id_hilo}** · consulta su estado más abajo, en *Seguimiento de expediente*.\n\n"
                f"Motivos: {'; '.join(estado.values['motivos'])}")
    return estado.values.get("respuesta", "")


def seguimiento(id_hilo):
    """El cliente consulta su expediente: pendiente de aprobación o respuesta final."""
    id_hilo = (id_hilo or "").strip()
    if not id_hilo:
        return "Escribe tu número de expediente (WEB-...)."
    estado = APP.get_state(config(id_hilo))
    if not estado.values:
        return f"No existe el expediente {id_hilo}."
    if "supervisor" in estado.next:
        return f"**{id_hilo}**: pendiente de aprobación del Supervisor de logística."
    return f"**{id_hilo}**: {estado.values.get('respuesta', '')}"


# ---------- Pestaña Supervisor ----------

def expedientes_pendientes():
    """Expedientes pausados en el nodo supervisor, leídos del checkpoint."""
    hilos = {c.config["configurable"]["thread_id"] for c in APP.checkpointer.list(None)}
    pendientes = {}
    for id_hilo in sorted(hilos):
        estado = APP.get_state(config(id_hilo))
        if "supervisor" in estado.next:
            pendientes[id_hilo] = estado.values
    return pendientes


def actualizar():
    pendientes = expedientes_pendientes()
    filas = [[h, v["cliente_id"], f"{v['cantidad']} {v['sku']}", v["fecha"], "; ".join(v["motivos"])]
             for h, v in pendientes.items()]
    return filas, gr.Dropdown(choices=list(pendientes), value=None), ""


def resumen(id_hilo):
    """Muestra el pedido antes de decidir: evita aprobar el expediente equivocado (riesgo de D11)."""
    if not id_hilo:
        return ""
    v = expedientes_pendientes().get(id_hilo)
    if not v:
        return "Ese expediente ya no está pendiente."
    return (f"**Vas a decidir:** {v['cantidad']} {v['sku']} para {v['cliente_id']}, entrega el {v['fecha']} · "
            f"costo del despacho extraordinario: {costo_extraordinario} USD.")


def decidir(id_hilo, decision):
    if not id_hilo or id_hilo not in expedientes_pendientes():
        filas, desplegable, _ = actualizar()
        return filas, desplegable, "Selecciona un expediente pendiente."
    final = APP.invoke(Command(resume=decision), config(id_hilo))
    filas, desplegable, _ = actualizar()
    return filas, desplegable, f"**{id_hilo}** → {final['respuesta']}"


# ---------- Interfaz ----------

with gr.Blocks(title="AndesSupply · Despachos") as demo:
    gr.Markdown(f"# AndesSupply · Asistente de despachos\n"
                f"**{CASO_ID}** · semilla {SEMILLA} · capacidad {capacidad_diaria} unidades/día · "
                f"ventana {ventana_entrega_dias} días hábiles · despacho extraordinario {costo_extraordinario} USD")

    with gr.Tab("Cliente / Vendedor"):
        gr.ChatInterface(atender, examples=EJEMPLOS)
        with gr.Row():
            numero = gr.Textbox(label="Seguimiento de expediente", placeholder="WEB-...", scale=3)
            boton_consultar = gr.Button("Consultar estado", scale=1)
        estado_pedido = gr.Markdown()
        boton_consultar.click(seguimiento, inputs=numero, outputs=estado_pedido)

    with gr.Tab("Supervisor de logística"):
        gr.Markdown("Expedientes pausados que esperan tu decisión.")
        boton_actualizar = gr.Button("Actualizar pendientes")
        tabla = gr.Dataframe(headers=COLUMNAS, interactive=False)
        expediente = gr.Dropdown(label="Expediente", choices=[])
        detalle = gr.Markdown()
        with gr.Row():
            boton_aprobar = gr.Button("Aprobar", variant="primary")
            boton_rechazar = gr.Button("Rechazar", variant="stop")
        resultado = gr.Markdown()

        boton_actualizar.click(actualizar, outputs=[tabla, expediente, resultado])
        expediente.change(resumen, inputs=expediente, outputs=detalle)
        boton_aprobar.click(lambda h: decidir(h, "aprobar"), inputs=expediente, outputs=[tabla, expediente, resultado])
        boton_rechazar.click(lambda h: decidir(h, "rechazar"), inputs=expediente, outputs=[tabla, expediente, resultado])
        demo.load(actualizar, outputs=[tabla, expediente, resultado])


if __name__ == "__main__":
    usuario, clave = os.getenv("APP_USUARIO"), os.getenv("APP_CLAVE")
    if os.getenv("SPACE_ID") and not (usuario and clave):
        raise SystemExit("En Hugging Face la app exige APP_USUARIO y APP_CLAVE como secretos: no se publica sin contraseña.")
    demo.launch(auth=(usuario, clave) if usuario and clave else None)
