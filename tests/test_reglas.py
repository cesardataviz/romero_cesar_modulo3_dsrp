# Pruebas de las reglas de negocio (Python puro, sin base de datos ni API).
from datetime import date

from config_caso import capacidad_diaria, costo_extraordinario, ventana_entrega_dias
from reglas import evaluar_pedido, fecha_despacho, fecha_minima_entrega


def test_parametros_de_la_semilla_9911():
    assert (capacidad_diaria, ventana_entrega_dias, costo_extraordinario) == (21, 5, 300)


def test_fecha_minima_segun_ciudad():
    assert fecha_minima_entrega(0) == date(2026, 10, 19)  # Lima
    assert fecha_minima_entrega(2) == date(2026, 10, 21)  # Arequipa


def test_caso_base_es_excepcion_con_dos_motivos():
    r = evaluar_pedido(12, "2026-10-15", stock=18, libres_en_despacho=9, dias_transito=0)
    assert r["decision"] == "EXCEPCION"
    assert len(r["motivos"]) == 2
    assert r["requiere"] == "Supervisor logística"


def test_pedido_normal_aprobado():
    assert fecha_despacho(date(2026, 10, 22), 2) == date(2026, 10, 20)
    r = evaluar_pedido(5, "2026-10-22", stock=10, libres_en_despacho=12, dias_transito=2)
    assert r["decision"] == "APROBADO"


def test_stock_insuficiente_se_rechaza():
    r = evaluar_pedido(6, "2026-10-23", stock=4, libres_en_despacho=21, dias_transito=3)
    assert r["decision"] == "RECHAZADO"


def test_sabado_se_rechaza():
    r = evaluar_pedido(2, "2026-10-17", stock=18, libres_en_despacho=21, dias_transito=0)
    assert r["decision"] == "RECHAZADO"
