# USO_IA · LOG-009 · Logística · Semilla 9911

Uso la IA como copiloto para entender conceptos, resolver dudas y proponer estructuras.
Las decisiones, ejecuciones y evidencias son mías.

## 1. Herramientas usadas

- **Claude** (Claude Code, app de escritorio): copiloto de aprendizaje, diseño y código.
- **OpenAI** (`text-embedding-3-small`, `gpt-6-luna`): parte del sistema (embeddings del RAG, router y agente MCP), no como asistente.

## 2. En qué me asistió la IA

| Etapa | Tipo de asistencia |
|---|---|
| Inicio | Comprender el enunciado y organizar el trabajo por hitos |
| Configuración del entorno | Creación del proyecto con uv y resolución de errores de terminal |
| Parámetros del caso | Propuesta inicial de `config_caso.py` y explicación de cómo funciona la semilla |
| Evidencias | Estructura para documentar las pruebas de reproducibilidad |
| Diseño de datos | Propuesta de tablas, análisis de riesgos y generación de datos de ejemplo |
| Carga a SQLite | Propuesta de `cargar_datos.py` y explicación de SQL parametrizado |
| Clasificación de solicitudes | Propuesta de solicitudes candidatas y revisión de mi clasificación |
| Consultas SQL, Tools y Reglas | Propuesta de `consultas_sql.py`, `tools.py` y `reglas.py`, y explicación del código |
| RAG y Router | Propuesta de `rag.py`, `router.py` y `evaluar_router.py`; verificación de modelos y precios vigentes |
| Pruebas automáticas | Generación de las pruebas pytest en `tests/` (simulan la API, sin costo) |
| Workflow y HITL | Explicación del State, `interrupt()`, checkpoint y retry; propuesta de `workflow.py` |
| MCP | Propuesta de `mcp_servidor.py`, `mcp_cliente.py` y `agente_mcp.py` |
| Integración y cierre | Propuesta de `demo_e2e.py`, diagramas y lista de limitaciones |

## 3. Tres prompts representativos

1. *"Quisiera hacerlo con embeddings, pero también conocer cómo hacerlo con TF-IDF. ¿No sería con chunks o me estoy confundiendo con conceptos?"* → La IA separó los pasos del RAG (chunking → representación → búsqueda). Decidí comparar ambos métodos y elegir embeddings con evidencia (D6).
2. *"En las preguntas ya estamos etiquetando a qué ruta va. ¿Eso lo usaría el LLM cuando no esté seguro?"* → Entendí que las etiquetas son un solucionario que el router no ve; luego corregí dos etiquetas cuando el router tenía razón (D9).
3. *"Prefiero que utilices desde el SQLite, no reconstruyas la base desde los CSV."* → La IA ajustó el demo y señaló que eso contradecía mi decisión D1; actualicé D1 con la nueva mitigación.

## 4. Qué modifiqué yo

- Ajusté los rangos de los parámetros del caso según mi criterio.
- Decidí incluir la ciudad de destino en el cálculo del plazo de entrega.
- Clasifiqué yo las solicitudes; la IA corrigió 7 y acepté las correcciones tras entenderlas.
- Detecté que un cliente inexistente y uno puntual daban el mismo resultado y propuse validar su existencia.
- Elegí proveedor de embeddings, mejora de chunks, tipo de router y criterio de fechas; corregí etiquetas del router cuando el sistema tenía razón.
- Definí qué capacidades exponer por MCP (mínimo privilegio) y propuse despachar antes cuando no hay capacidad.

## 5. Sugerencias rechazadas

- **Interpretar "el jueves" y "el 22" como su próxima fecha** (opción B del router). La rechacé y elegí un criterio estricto: es preferible preguntar una vez que prometer una fecha mal interpretada (D9).
- **Usar Voyage AI** para los embeddings (gratis, recomendado por Anthropic). Elegí OpenAI porque ya tenía cuenta y un solo proveedor simplifica el control de costos (D6).
- **Reconstruir la base en cada ejecución del demo.** Preferí usar la base existente y reconstruirla solo al editar un CSV (D1 actualizada).

## 6. Errores de la IA detectados

- **Las pruebas fallaron por la IA:** al ejecutar `pytest`, recibí `PermissionError: ... andessupply.db está siendo utilizado por otro proceso`. La causa fue que la IA ejecutó las pruebas en mi proyecto al mismo tiempo que yo; ambas intentaban borrar y reconstruir la base.
- **Código basado en una versión antigua de MCP:** la IA asumió la API de `mcp` 1.x (`FastMCP`, `isError`), pero la versión instalada era la 2.x (`MCPServer`, `is_error`). El error apareció al ejecutar el cliente y se corrigió.
- **El router "se tragaba" los errores:** el código propuesto en el Hito 2 atrapaba todos los errores de OpenAI y devolvía CLARIFY, así que el retry del Hito 4 nunca se habría activado. Se detectó al diseñar el retry y se corrigió (D12).

## 7. Cómo validé antes de confiar

- Ejecuté yo mismo cada componente y comparé la salida con lo esperado.
- Hice predicciones antes de ejecutar y analicé cuándo fallaban (p. ej., el agente consultó la capacidad del día 20 y no del 22, como yo predije).
- Revisé las evidencias contra el código: así detecté que `config_caso.py` estaba commiteado con el orden de la semilla cambiado.
- Mantuve 43 pruebas automáticas que se ejecutan sin costo antes de cada commit.
- Pedí verificar en la documentación oficial modelos, precios y versiones de librerías antes de usarlos.
