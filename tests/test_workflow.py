# Pruebas del workflow (§12): ruta directa, ruta HITL, aprobar y rechazar. El router LLM se simula.
import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

import router
import workflow
from router import Decision

CASO_BASE = "C-1003 necesita 12 EDGE-ORIN para el jueves 15 de octubre."


@pytest.fixture
def app(monkeypatch):
    def llm_simulado(solicitud):
        return Decision(destino="TOOLS", confianza=0.95, cliente_id="C-1003", sku="EDGE-ORIN",
                        cantidad=12, fecha="2026-10-15", motivo="simulado")

    monkeypatch.setattr(router, "clasificar_con_llm", llm_simulado)
    return workflow.construir_workflow(InMemorySaver())  # checkpoint en memoria para las pruebas


def config(id_hilo):
    return {"configurable": {"thread_id": id_hilo}}


def test_ruta_directa_sin_herramientas(app):
    final = app.invoke({"solicitud": "Hola, ¿qué puedes hacer por mí?"}, config("t-directa"))
    assert final["destino"] == "DIRECT"
    assert "decision" not in final  # no pasó por validar, consultar ni evaluar


def test_caso_base_se_pausa_en_el_supervisor(app):
    app.invoke({"solicitud": CASO_BASE}, config("t-pausa"))
    estado = app.get_state(config("t-pausa"))
    assert estado.next == ("supervisor",)
    assert estado.values["decision"] == "EXCEPCION"


def test_aprobar_reanuda_con_el_mismo_id_hilo(app):
    app.invoke({"solicitud": CASO_BASE}, config("t-aprobar"))
    final = app.invoke(Command(resume="aprobar"), config("t-aprobar"))
    assert final["decision"] == "APROBADO_EXTRAORDINARIO"
    assert "300 USD" in final["respuesta"]


def test_rechazar_ofrece_la_fecha_estandar_con_capacidad(app):
    app.invoke({"solicitud": CASO_BASE}, config("t-rechazar"))
    final = app.invoke(Command(resume="rechazar"), config("t-rechazar"))
    assert final["aprobacion"] == "rechazar"
    assert "2026-10-20" in final["respuesta"]


def test_otro_id_hilo_no_encuentra_el_flujo_pausado(app):
    app.invoke({"solicitud": CASO_BASE}, config("t-original"))
    assert app.get_state(config("t-otro")).values == {}


def test_respuesta_no_valida_del_supervisor_no_autoriza(app):
    app.invoke({"solicitud": CASO_BASE}, config("t-invalida"))
    final = app.invoke(Command(resume="quizás"), config("t-invalida"))
    assert final["aprobacion"] == "rechazar"
