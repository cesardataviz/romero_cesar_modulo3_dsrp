# demo_e2e.py
# Caso end-to-end reproducible (Hito 6): integra semilla, datos, router, fuentes (RAG, SQL, Tools),
# reglas, workflow con HITL y checkpoint, y MCP (cliente puro + agente). Un solo comando.
import asyncio
import sys
from datetime import datetime

import agente_mcp
import mcp_cliente
import workflow
from cargar_datos import DB_PATH, reconstruir_base
from config_caso import mostrar_config

CASO_BASE = "C-1003 necesita 12 EDGE-ORIN para el jueves 15 de octubre."
CONSULTAS = [
    "¿Quién autoriza un envío urgente?",          # RAG (LLM en el router + embeddings)
    "¿Cuántas entregas tardías tuvo C-1002?",     # SQL (regla del router, sin LLM)
]


def titulo(texto):
    print(f"\n{'=' * 78}\n{texto}\n{'=' * 78}")


def main(decision_supervisor):
    titulo("1 · Caso y semilla")
    mostrar_config()

    titulo("2 · Datos: base SQLite")
    if DB_PATH.exists():
        print(f"Se usa la base existente: {DB_PATH.name}")
    else:
        print(f"No existe {DB_PATH.name}: se crea desde los CSV")
        reconstruir_base()

    app = workflow.abrir_workflow()
    sello = datetime.now().strftime("%Y%m%d-%H%M%S")

    titulo("3 · Router + fuentes: consultas que no son pedidos")
    for i, consulta in enumerate(CONSULTAS, start=1):
        workflow.iniciar(app, f"E2E-{sello}-C{i}", consulta)

    id_hilo = f"E2E-{sello}-PEDIDO"
    titulo(f"4 · Caso base: router → validar → Tools → Reglas → HITL  (id_hilo={id_hilo})")
    workflow.iniciar(app, id_hilo, CASO_BASE)

    titulo("5 · Estado guardado en el checkpoint (data/checkpoints.db)")
    workflow.ver_estado(app, id_hilo)

    titulo(f"6 · Decisión del Supervisor de logística: {decision_supervisor} (mismo id_hilo)")
    workflow.reanudar(app, id_hilo, decision_supervisor)

    titulo("7 · MCP: cliente puro, sin LLM (las mismas capacidades, desde afuera)")
    asyncio.run(mcp_cliente.main())

    titulo("8 · MCP: agente con LLM (consulta compuesta)")
    asyncio.run(agente_mcp.main(agente_mcp.PREGUNTA_POR_DEFECTO))


if __name__ == "__main__":
    decision = sys.argv[1] if len(sys.argv) > 1 else "aprobar"
    if decision not in ("aprobar", "rechazar"):
        print("Uso: uv run demo_e2e.py [aprobar|rechazar]")
    else:
        main(decision)
