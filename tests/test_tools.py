# Pruebas de las Tools (estado actual) y del manejo de datos inexistentes.
from tools import consultar_capacidad, consultar_cliente, consultar_stock, consultar_transito


def test_stock_de_edge_orin():
    resultado = consultar_stock("EDGE-ORIN")
    assert resultado["ok"] is True
    assert resultado["stock_disponible"] == 18


def test_sku_inexistente():
    resultado = consultar_stock("DRONE-X1")
    assert resultado["ok"] is False
    assert "no existe" in resultado["motivo"]


def test_cliente_inexistente():
    assert consultar_cliente("C-1099")["ok"] is False


def test_capacidad_libre_del_jueves_15():
    resultado = consultar_capacidad("2026-10-15")
    assert (resultado["capacidad_diaria"], resultado["comprometidas"], resultado["libres"]) == (21, 12, 9)


def test_ciudad_sin_transito_registrado():
    assert consultar_transito("Arequipa") == {"ok": True, "ciudad": "Arequipa", "dias_transito": 2}
    assert consultar_transito("Iquitos")["ok"] is False
