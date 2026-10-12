# Pruebas del router sin llamar a la API: las reglas son deterministas y el LLM se simula.
import openai
import pytest

import router
from router import Decision


def decision_llm(**cambios):
    datos = dict(destino="TOOLS", confianza=0.95, cliente_id="C-1003", sku="EDGE-ORIN",
                 cantidad=12, fecha="2026-10-15", motivo="simulado")
    return Decision(**{**datos, **cambios})


@pytest.mark.parametrize("solicitud, destino", [
    ("Hola, ¿qué puedes hacer por mí?", "DIRECT"),
    ("¿Cuántas entregas tardías ha tenido Agroindustrial del Norte?", "SQL"),
    ("¿Cuál es la política para un despacho extraordinario?", "RAG"),
])
def test_reglas_deterministas(solicitud, destino):
    r = router.enrutar(solicitud)
    assert (r["destino"], r["origen"], r["confianza"]) == (destino, "regla", 1.0)


def test_llm_con_confianza_baja_va_a_clarify(monkeypatch):
    monkeypatch.setattr(router, "clasificar_con_llm", lambda s: decision_llm(confianza=0.5))
    assert router.enrutar("C-1003 necesita 12 EDGE-ORIN el jueves 15")["destino"] == "CLARIFY"


def test_datos_invalidos_del_llm_se_descartan(monkeypatch):
    monkeypatch.setattr(router, "clasificar_con_llm",
                        lambda s: decision_llm(cliente_id="cliente 3", fecha="el jueves"))
    r = router.enrutar("pedido de prueba")
    assert r["cliente_id"] is None and r["fecha"] is None
    assert r["destino"] == "TOOLS"  # sigue teniendo SKU


def test_si_el_llm_falla_se_detiene_en_clarify(monkeypatch):
    def llm_caido(solicitud):
        raise openai.APIConnectionError(request=None)

    monkeypatch.setattr(router, "clasificar_con_llm", llm_caido)
    r = router.enrutar("C-1008 necesita 6 CAM-GIGE5 para el viernes 23.")
    assert (r["destino"], r["origen"]) == ("CLARIFY", "respaldo")
