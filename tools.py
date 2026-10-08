# tools.py
# Tools: consultan el ESTADO ACTUAL (clientes, stock, capacidad, tránsito).
# Solo buscan datos; las decisiones las toman las reglas.
from config_caso import capacidad_diaria
from consultas_sql import consultar


def consultar_cliente(cliente_id):
    """Datos del cliente (ciudad y tipo). Indica si no existe."""
    filas = consultar(
        "SELECT cliente_id, nombre, ciudad, tipo FROM clientes WHERE cliente_id = ?",
        (cliente_id,),
    )
    if not filas:
        return {"ok": False, "motivo": f"El cliente {cliente_id} no existe"}
    return {"ok": True, **filas[0]}


def consultar_stock(sku):
    """Stock disponible de un SKU. Indica si el SKU no existe."""
    filas = consultar(
        """SELECT p.sku, p.nombre, i.stock_disponible
           FROM productos p
           JOIN inventario i ON i.sku = p.sku
           WHERE p.sku = ?""",
        (sku,),
    )
    if not filas:
        return {"ok": False, "motivo": f"El SKU {sku} no existe"}
    return {"ok": True, **filas[0]}


def consultar_capacidad(fecha):
    """Capacidad de despacho de un día: total, comprometida y libre."""
    filas = consultar(
        "SELECT unidades_comprometidas FROM despachos_programados WHERE fecha = ?",
        (fecha,),
    )
    comprometidas = filas[0]["unidades_comprometidas"] if filas else 0
    return {
        "ok": True,
        "fecha": fecha,
        "capacidad_diaria": capacidad_diaria,
        "comprometidas": comprometidas,
        "libres": max(0, capacidad_diaria - comprometidas),
    }


def consultar_transito(ciudad):
    """Días de tránsito hacia una ciudad. Indica si la ciudad no está registrada."""
    filas = consultar("SELECT dias_transito FROM ciudades WHERE ciudad = ?", (ciudad,))
    if not filas:
        return {"ok": False, "motivo": f"La ciudad {ciudad} no tiene tránsito registrado"}
    return {"ok": True, "ciudad": ciudad, "dias_transito": filas[0]["dias_transito"]}


if __name__ == "__main__":
    print("1) Cliente C-1003:", consultar_cliente("C-1003"))
    print("2) Cliente C-1099:", consultar_cliente("C-1099"))
    print("3) Stock EDGE-ORIN:", consultar_stock("EDGE-ORIN"))
    print("4) Stock DRONE-X1:", consultar_stock("DRONE-X1"))
    print("5) Capacidad jueves 2026-10-15:", consultar_capacidad("2026-10-15"))
    print("6) Tránsito a Arequipa:", consultar_transito("Arequipa"))
    print("7) Tránsito a Iquitos:", consultar_transito("Iquitos"))