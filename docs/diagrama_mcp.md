# MCP: antes y después

## Antes de MCP (acoplado)

Cada aplicación que quiere consultar stock o capacidad debe importar el código Python del proyecto y acceder directamente a la base de datos.

```mermaid
flowchart LR
    P["Portal web"] -->|importa tools.py| T["tools.py · reglas.py · config_caso.py"]
    C["Chatbot de ventas<br/>(otro lenguaje)"] -.->|no puede importar Python| T
    A["Agente LangGraph"] -->|importa| T
    P -->|lee/escribe| DB[("andessupply.db<br/>todas las tablas")]
    C -.->|acceso directo| DB
    T --> DB
```

Problemas: dependencia del lenguaje (Python), cada cambio interno rompe a los consumidores, la lógica se copia y diverge, y todos acceden a toda la base (incluso para escribir).

## Con MCP (desacoplado, mínimo privilegio)

```mermaid
flowchart LR
    CP["mcp_cliente.py<br/>cliente puro, sin LLM"] -->|list_tools / call_tool| S
    AG["agente_mcp.py<br/>LLM decide qué tool usar"] -->|list_tools / call_tool| S
    OT["Otras apps / Claude Desktop<br/>(cualquier lenguaje)"] -->|protocolo MCP| S
    S["mcp_servidor.py · stdio<br/>4 Tools de solo lectura<br/>2 Resources (políticas)"] --> T["tools.py · reglas.py"]
    T --> DB[("andessupply.db")]
    X["ejecutar_sql · aprobar_despacho<br/>actualizar_stock · historial_ventas"]:::bloqueado
    classDef bloqueado stroke-dasharray: 5 5
```

Los consumidores solo ven el menú publicado (`consultar_stock`, `consultar_capacidad`, `consultar_transito`, `consultar_fecha_despacho`, `politica://despacho`, `politica://despacho-extraordinario`). Lo que no se publica, no existe para ellos.
