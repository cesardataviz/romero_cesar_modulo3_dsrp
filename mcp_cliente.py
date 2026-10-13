# mcp_cliente.py
# Cliente MCP PURO (sin LLM): descubre y usa las capacidades del servidor por stdio.
# No importa tools.py ni toca la base de datos: solo conoce el "menú" que publica el servidor.
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVIDOR = StdioServerParameters(command=sys.executable,
                                 args=[str(Path(__file__).parent / "mcp_servidor.py")])


def mostrar(resultado):
    """Contenido de una respuesta de call_tool como diccionario (o texto si no es JSON)."""
    texto = resultado.content[0].text
    if resultado.is_error:
        return f"ERROR: {texto}"
    try:
        return json.loads(texto)  # el servidor responde JSON
    except json.JSONDecodeError:
        return texto


async def main():
    async with stdio_client(SERVIDOR) as (lectura, escritura):
        async with ClientSession(lectura, escritura) as sesion:
            await sesion.initialize()

            print("list_tools:")
            for herramienta in (await sesion.list_tools()).tools:
                print(f"  - {herramienta.name}: {herramienta.description.splitlines()[0]}")

            print("list_resources:")
            for recurso in (await sesion.list_resources()).resources:
                print(f"  - {recurso.uri} · {recurso.name}")

            print("call_tool:")
            for nombre, argumentos in [
                ("consultar_stock", {"sku": "EDGE-ORIN"}),
                ("consultar_capacidad", {"fecha": "2026-10-15"}),
                ("consultar_capacidad", {"fecha": "2026-10-17"}),
                ("consultar_transito", {"ciudad": "Iquitos"}),
            ]:
                print(f"  {nombre}({argumentos}) → {mostrar(await sesion.call_tool(nombre, argumentos))}")

            politica = await sesion.read_resource("politica://despacho-extraordinario")
            print(f"read_resource politica://despacho-extraordinario → {politica.contents[0].text.splitlines()[0]}")

            print("call_tool de una capacidad NO expuesta:")
            r = await sesion.call_tool("ejecutar_sql", {"sql": "SELECT * FROM ventas"})
            print(f"  ejecutar_sql → {mostrar(r)}")


if __name__ == "__main__":
    asyncio.run(main())
