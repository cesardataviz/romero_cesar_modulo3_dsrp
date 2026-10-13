# mcp_servidor.py
# Servidor MCP (stdio) de AndesSupply: expone capacidades de negocio de SOLO LECTURA (D13).
# Mínimo privilegio: 4 Tools de consulta + 2 Resources de políticas.
# No se exponen: SQL libre, escritura de stock, aprobación de despachos ni historial de ventas.
import contextlib
import sys
from datetime import date
from pathlib import Path

from mcp.server.mcpserver import MCPServer

import tools
from cargar_datos import DB_PATH, reconstruir_base
from reglas import es_dia_habil, fecha_despacho

POLITICAS_DIR = Path(__file__).parent / "data" / "politicas"

servidor = MCPServer(
    "andessupply-logistica",
    instructions="Consultas de despacho de AndesSupply (LOG-009): stock, capacidad diaria y días de "
                 "tránsito, más las políticas de despacho. Todas las capacidades son de solo lectura.",
)


@servidor.tool()
def consultar_stock(sku: str) -> dict:
    """Stock disponible de un producto (SKU, p. ej. EDGE-ORIN). Indica si el SKU no existe."""
    return tools.consultar_stock(sku)


@servidor.tool()
def consultar_capacidad(fecha: str) -> dict:
    """Capacidad de despacho de un día (AAAA-MM-DD): total, comprometida y libre. Indica si es día hábil."""
    try:
        dia = date.fromisoformat(fecha)
    except ValueError:
        return {"ok": False, "motivo": f"Fecha inválida: {fecha}. Usa el formato AAAA-MM-DD"}
    if not es_dia_habil(dia):  # D5: sábados y domingos no se despacha
        return {"ok": True, "fecha": fecha, "dia_habil": False, "libres": 0,
                "motivo": "No se despacha en fines de semana"}
    return {**tools.consultar_capacidad(fecha), "dia_habil": True}


@servidor.tool()
def consultar_transito(ciudad: str) -> dict:
    """Días de tránsito desde el almacén hasta una ciudad. Indica si la ciudad no está registrada."""
    return tools.consultar_transito(ciudad)


@servidor.tool()
def consultar_fecha_despacho(fecha_entrega: str, ciudad: str) -> dict:
    """Día en que debe salir del almacén un pedido para llegar a una ciudad en la fecha de entrega (AAAA-MM-DD).

    Úsala en lugar de calcular fechas: resta los días de tránsito en días hábiles (reglas de negocio).
    """
    try:
        entrega = date.fromisoformat(fecha_entrega)
    except ValueError:
        return {"ok": False, "motivo": f"Fecha inválida: {fecha_entrega}. Usa el formato AAAA-MM-DD"}
    transito = tools.consultar_transito(ciudad)
    if not transito["ok"]:
        return transito
    if not es_dia_habil(entrega):
        return {"ok": False, "motivo": f"{fecha_entrega} no es día hábil: no se entrega en fines de semana"}
    despacho = fecha_despacho(entrega, transito["dias_transito"])
    return {"ok": True, "fecha_entrega": fecha_entrega, "ciudad": ciudad,
            "dias_transito": transito["dias_transito"], "fecha_despacho": despacho.isoformat()}


@servidor.resource("politica://despacho", name="Política de despacho estándar", mime_type="text/markdown")
def politica_despacho() -> str:
    return (POLITICAS_DIR / "politica_despacho.md").read_text(encoding="utf-8")


@servidor.resource("politica://despacho-extraordinario", name="Política de despacho extraordinario",
                   mime_type="text/markdown")
def politica_despacho_extraordinario() -> str:
    return (POLITICAS_DIR / "politica_despacho_extraordinario.md").read_text(encoding="utf-8")


if __name__ == "__main__":
    if not DB_PATH.exists():
        with contextlib.redirect_stdout(sys.stderr):  # stdout queda reservado para el protocolo MCP
            reconstruir_base()
    servidor.run()  # transporte stdio
