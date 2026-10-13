# Prueba del agente MCP (§12: "una consulta compuesta") sin gastar: el LLM se simula,
# pero las herramientas se ejecutan de verdad en el servidor MCP (en memoria).
import asyncio
import json
from types import SimpleNamespace

import mcp

import agente_mcp
import mcp_servidor


def llamada(nombre, argumentos, call_id):
    return SimpleNamespace(type="function_call", name=nombre, arguments=json.dumps(argumentos), call_id=call_id)


class LLMSimulado:
    """Imita al LLM: 1.ª vuelta pide 4 herramientas; 2.ª vuelta responde con los datos que recibió."""

    def __init__(self):
        self.vueltas = []
        self.responses = self

    def create(self, **parametros):
        self.vueltas.append(parametros)
        uso = SimpleNamespace(input_tokens=100, output_tokens=20)
        if len(self.vueltas) == 1:
            pedidas = [
                llamada("consultar_stock", {"sku": "PLC-S7M"}, "c1"),
                llamada("consultar_transito", {"ciudad": "Arequipa"}, "c2"),
                llamada("consultar_fecha_despacho", {"fecha_entrega": "2026-10-22", "ciudad": "Arequipa"}, "c3"),
                llamada("consultar_capacidad", {"fecha": "2026-10-20"}, "c4"),
            ]
            return SimpleNamespace(output=pedidas, usage=uso, output_text="")
        resultados = [m for m in parametros["input"] if isinstance(m, dict) and m.get("type") == "function_call_output"]
        return SimpleNamespace(output=[], usage=uso, output_text=f"{len(resultados)} datos recibidos")


def test_consulta_compuesta_usa_las_herramientas_del_servidor_mcp():
    llm = LLMSimulado()

    async def ejecutar():
        async with mcp.Client(mcp_servidor.servidor) as sesion:
            return await agente_mcp.preguntar(sesion, "¿Pueden despachar 5 PLC-S7M a Arequipa el 22?", llm)

    respuesta = asyncio.run(ejecutar())
    assert respuesta == "4 datos recibidos"
    nombres = {h["name"] for h in llm.vueltas[0]["tools"]}
    assert nombres == {"consultar_stock", "consultar_capacidad", "consultar_transito", "consultar_fecha_despacho"}
    salidas = {m["call_id"]: json.loads(m["output"]) for m in llm.vueltas[1]["input"]
               if isinstance(m, dict) and m.get("type") == "function_call_output"}
    assert salidas["c1"]["stock_disponible"] == 10
    assert salidas["c3"]["fecha_despacho"] == "2026-10-20"
    assert salidas["c4"]["libres"] == 12
