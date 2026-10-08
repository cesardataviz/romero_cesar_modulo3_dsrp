# reglas.py
# Reglas de negocio: decisiones OBJETIVAS en Python puro.
# No consultan datos: reciben lo que devuelven las Tools y deciden.
from datetime import date, timedelta

from config_caso import FECHA_REFERENCIA, costo_extraordinario, ventana_entrega_dias


def es_dia_habil(fecha):
    """Lunes a viernes. Los feriados quedan fuera de alcance."""
    return fecha.weekday() < 5


def sumar_dias_habiles(fecha, dias):
    """Avanza (o retrocede, si dias es negativo) esa cantidad de días hábiles."""
    paso = 1 if dias >= 0 else -1
    restantes = abs(dias)
    while restantes > 0:
        fecha += timedelta(days=paso)
        if es_dia_habil(fecha):
            restantes -= 1
    return fecha


def fecha_minima_entrega(dias_transito):
    """Hoy + ventana estándar + días de tránsito, en días hábiles (D2)."""
    hoy = date.fromisoformat(FECHA_REFERENCIA)
    return sumar_dias_habiles(hoy, ventana_entrega_dias + dias_transito)


def fecha_despacho(fecha_entrega, dias_transito):
    """Día en que debe salir del almacén para llegar en la fecha de entrega."""
    return sumar_dias_habiles(fecha_entrega, -dias_transito)


def evaluar_pedido(cantidad, fecha_pedida, stock, libres_en_despacho, dias_transito):
    """Decide: APROBADO, EXCEPCION (requiere supervisor) o RECHAZADO."""
    fecha = date.fromisoformat(fecha_pedida)

    if not es_dia_habil(fecha):
        return {"decision": "RECHAZADO", "motivos": [f"{fecha} no es día hábil (D5)"]}
    if cantidad > stock:
        return {"decision": "RECHAZADO", "motivos": [f"Stock insuficiente: pide {cantidad}, hay {stock}"]}

    motivos = []
    minima = fecha_minima_entrega(dias_transito)
    if fecha < minima:
        motivos.append(f"Fecha pedida {fecha} es anterior a la mínima {minima}")
    if cantidad > libres_en_despacho:
        motivos.append(f"Capacidad insuficiente: pide {cantidad}, quedan {libres_en_despacho} libres")

    if motivos:
        return {
            "decision": "EXCEPCION",
            "motivos": motivos,
            "requiere": "Supervisor logística",
            "costo_extraordinario": costo_extraordinario,
        }
    return {"decision": "APROBADO", "motivos": [], "fecha_entrega": str(fecha)}


if __name__ == "__main__":
    # Datos tomados de las Tools (Evidencia 4). Las reglas no consultan nada.
    print("Fecha mínima Lima (0 días tránsito):", fecha_minima_entrega(0))
    print("Fecha mínima Arequipa (2 días):", fecha_minima_entrega(2))

    print("1) C-1003 · 12 EDGE-ORIN · jueves 15 · Lima:",
          evaluar_pedido(12, "2026-10-15", stock=18, libres_en_despacho=9, dias_transito=0))
    print("2) C-1004 · 5 PLC-S7M · 22 · Arequipa (despacho el",
          fecha_despacho(date(2026, 10, 22), 2), "):",
          evaluar_pedido(5, "2026-10-22", stock=10, libres_en_despacho=12, dias_transito=2))
    print("3) C-1008 · 6 CAM-GIGE5 · viernes 23:",
          evaluar_pedido(6, "2026-10-23", stock=4, libres_en_despacho=21, dias_transito=3))
    print("4) Entrega un sábado 17:",
          evaluar_pedido(2, "2026-10-17", stock=18, libres_en_despacho=21, dias_transito=0))