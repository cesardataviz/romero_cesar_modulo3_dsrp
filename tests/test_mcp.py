# Pruebas del servidor MCP sin LLM (§12): list_tools, call_tool y read_resource, en memoria.
import asyncio
import json

import mcp

import mcp_servidor


def con_cliente(accion):
    """Abre un cliente MCP en memoria contra el servidor y ejecuta la acción."""
    async def ejecutar():
        async with mcp.Client(mcp_servidor.servidor) as cliente:
            return await accion(cliente)

    return asyncio.run(ejecutar())


def test_list_tools_expone_solo_las_cuatro_consultas():
    async def accion(cliente):
        return sorted(t.name for t in (await cliente.list_tools()).tools)

    assert con_cliente(accion) == ["consultar_capacidad", "consultar_fecha_despacho",
                                   "consultar_stock", "consultar_transito"]


def test_call_tool_consultar_stock():
    async def accion(cliente):
        return json.loads((await cliente.call_tool("consultar_stock", {"sku": "EDGE-ORIN"})).content[0].text)

    assert con_cliente(accion)["stock_disponible"] == 18


def test_capacidad_en_fin_de_semana_no_se_ofrece():
    async def accion(cliente):
        return json.loads((await cliente.call_tool("consultar_capacidad", {"fecha": "2026-10-17"})).content[0].text)

    resultado = con_cliente(accion)
    assert resultado["dia_habil"] is False and resultado["libres"] == 0


def test_fecha_de_despacho_la_calcula_python():
    async def accion(cliente):
        argumentos = {"fecha_entrega": "2026-10-22", "ciudad": "Arequipa"}
        return json.loads((await cliente.call_tool("consultar_fecha_despacho", argumentos)).content[0].text)

    assert con_cliente(accion)["fecha_despacho"] == "2026-10-20"  # 22 de octubre − 2 días hábiles


def test_read_resource_politica():
    async def accion(cliente):
        return (await cliente.read_resource("politica://despacho-extraordinario")).contents[0].text

    assert "Supervisor de logística" in con_cliente(accion)


def test_sql_libre_no_esta_expuesto():
    async def accion(cliente):
        return await cliente.call_tool("ejecutar_sql", {"sql": "SELECT * FROM ventas"})

    assert con_cliente(accion).is_error is True
