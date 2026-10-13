# agente_mcp.py
# Agente que consume el MISMO servidor MCP que mcp_cliente.py.
# El LLM decide qué Tools usar y redacta la respuesta; los datos y los cálculos los hace el servidor (Python).
import asyncio
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import openai
from openai import OpenAI

from config_caso import CASO_ID, FECHA_REFERENCIA, SEMILLA

load_dotenv()  # lee .env y carga OPENAI_API_KEY

MODELO_AGENTE = "gpt-6-luna"
PRECIO_ENTRADA, PRECIO_SALIDA = 0.10, 0.50  # USD por millón de tokens (gpt-6-luna)
MAX_PASOS = 6  # límite de vueltas: evita que el agente quede en un bucle de herramientas

SERVIDOR = StdioServerParameters(command=sys.executable,
                                 args=[str(Path(__file__).parent / "mcp_servidor.py")])

INSTRUCCIONES = f"""Eres el asistente de despachos de AndesSupply. Hoy es lunes {FECHA_REFERENCIA}.
Responde SOLO con datos que devuelvan las herramientas; nunca inventes stock, capacidades ni fechas.
No calcules fechas tú mismo: para saber qué día sale un despacho usa consultar_fecha_despacho
y luego consulta la capacidad de ESE día. No puedes aprobar despachos extraordinarios: si la capacidad
no alcanza, indica que se requiere aprobación del Supervisor de logística.
Responde en español, en pocas líneas, mencionando los datos usados."""

PREGUNTA_POR_DEFECTO = ("¿Pueden despachar 5 PLC-S7M al cliente C-1004 en Arequipa para el jueves 22 de "
                        "octubre de 2026? Revisa stock, tránsito y capacidad.")


def herramientas_para_llm(herramientas_mcp):
    """Traduce el menú MCP (list_tools) al formato de herramientas del LLM. No se escribe nada a mano."""
    return [{"type": "function", "name": h.name, "description": h.description,
             "parameters": h.input_schema, "strict": False} for h in herramientas_mcp]


async def preguntar(sesion, pregunta, cliente_llm=None):
    """Bucle del agente: el LLM pide herramientas, el servidor MCP las ejecuta, hasta tener la respuesta."""
    cliente_llm = cliente_llm or OpenAI()
    herramientas = herramientas_para_llm((await sesion.list_tools()).tools)
    entrada = [{"role": "user", "content": pregunta}]
    tokens_entrada = tokens_salida = 0

    for _ in range(MAX_PASOS):
        respuesta = cliente_llm.responses.create(
            model=MODELO_AGENTE, instructions=INSTRUCCIONES, input=entrada,
            tools=herramientas, reasoning={"effort": "none"},
        )
        tokens_entrada += respuesta.usage.input_tokens
        tokens_salida += respuesta.usage.output_tokens
        llamadas = [item for item in respuesta.output if item.type == "function_call"]

        if not llamadas:  # el LLM ya no necesita más datos: esta es la respuesta final
            costo = (tokens_entrada * PRECIO_ENTRADA + tokens_salida * PRECIO_SALIDA) / 1_000_000
            print(f"  [costo] {tokens_entrada}+{tokens_salida} tokens ≈ {costo:.6f} USD")
            return respuesta.output_text

        entrada += respuesta.output  # se conserva lo que decidió el LLM
        for llamada in llamadas:
            argumentos = json.loads(llamada.arguments)
            resultado = await sesion.call_tool(llamada.name, argumentos)  # se ejecuta en el servidor MCP
            texto = resultado.content[0].text
            print(f"  [tool] {llamada.name}({argumentos}) → {json.dumps(json.loads(texto), ensure_ascii=False)}")
            entrada.append({"type": "function_call_output", "call_id": llamada.call_id, "output": texto})

    return "No pude completar la consulta en el número máximo de pasos."


async def main(pregunta):
    async with stdio_client(SERVIDOR) as (lectura, escritura):
        async with ClientSession(lectura, escritura) as sesion:
            await sesion.initialize()
            print(f"> {pregunta}")
            try:
                print(f"\n{await preguntar(sesion, pregunta)}")
            except openai.OpenAIError as error:
                print(f"  [ERROR] El LLM no está disponible ({type(error).__name__}). Las herramientas MCP "
                      f"siguen funcionando: pruébalas con uv run mcp_cliente.py")


if __name__ == "__main__":
    print(f"{CASO_ID} · semilla {SEMILLA} · agente MCP")
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else PREGUNTA_POR_DEFECTO))
