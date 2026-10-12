# Pruebas de las consultas SQL parametrizadas (historial).
from consultas_sql import cliente_existe, cumplimiento_entregas, entregas_tardias, historial_ventas


def test_entregas_tardias_de_c1002():
    tardias = entregas_tardias("C-1002")
    assert [t["venta_id"] for t in tardias] == ["V-0005", "V-0012"]
    assert [t["dias_retraso"] for t in tardias] == [6, 7]


def test_historial_de_c1003_desde_julio():
    ventas = historial_ventas("C-1003", "2026-07-12")
    assert [v["sku"] for v in ventas] == ["CAM-GIGE5", "EDGE-ORIN", "LENS-12MM"]


def test_cumplimiento_cliente_puntual():
    assert cumplimiento_entregas("C-1001") == {"total": 3, "a_tiempo": 3}


def test_cliente_inexistente_no_se_confunde_con_puntual():
    assert entregas_tardias("C-1099") == entregas_tardias("C-1001") == []
    assert cliente_existe("C-1001") is True
    assert cliente_existe("C-1099") is False


def test_sql_injection_no_altera_la_consulta():
    assert entregas_tardias("C-1002' OR '1'='1") == []
