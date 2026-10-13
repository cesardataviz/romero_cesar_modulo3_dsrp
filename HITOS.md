# HITOS · LOG-009 · Logística · Semilla 9911

## Hito 1 · Separar responsabilidades — ✅ completado

- **Qué se construyó:** proyecto con uv (Python 3.12) y `config_caso.py`: la semilla 9911 genera capacidad diaria (21), ventana de entrega (5 días) y costo extraordinario (300 USD).
- **Qué falló:** ejecutar desde una carpeta equivocada (`program not found`); al clasificar solicitudes confundí SQL con Tool y Tool con Regla.
- **Qué aprendí:** la semilla genera una secuencia pseudoaleatoria fija; cambiar el orden de las llamadas cambia los valores. SQL = historial, Tool = estado actual, Regla = decisión con datos; el SQL siempre va parametrizado (`?`).
- **Qué decisión cambió:** la ciudad de destino se incluye en el cálculo del plazo (D2); reclasifiqué 7 de mis 13 solicitudes tras revisarlas.
- **Evidencia:** EVIDENCIAS.md · Evidencias 1 y 2.
- **Datos:** 6 CSV en `data/` (clientes, ciudades, productos, inventario, ventas, despachos programados).
- **Carga:** `cargar_datos.py` reconstruye SQLite desde los CSV.
- **Clasificación:** 10 solicitudes en `docs/clasificacion_solicitudes.md`.

**Preguntas de razonamiento**
- **¿Qué decisiones NO necesitan un LLM?** Las reglas de negocio (plazos, capacidad, stock), las respuestas directas y la ejecución de SQL/Tools: son determinísticas. El LLM solo hace falta para entender el lenguaje natural: clasificar la solicitud y extraer cliente, SKU, cantidad y fecha.
- **¿Qué dato cambia frecuentemente y no debería vivir en un prompt?** El stock, la capacidad libre y los despachos programados. Deben consultarse en el momento; las políticas cambian poco y viven en documentos.
- **¿Qué información es documental y cuál transaccional?** Documental: políticas de despacho y despachos extraordinarios (RAG por chunks). Transaccional: ventas, entregas e inventario (SQL para historial, Tools para estado actual).

## Hito 2 · Router + RAG + SQL + Tools — ✅ completado

- **Qué se construyó:** `consultas_sql.py` con 3 consultas parametrizadas (entregas tardías, historial, cumplimiento) y `cliente_existe`; `tools.py` con 4 Tools semánticas (cliente, stock, capacidad, tránsito); `reglas.py` con la decisión APROBADO / EXCEPCION / RECHAZADO; `rag.py` con chunking por sección y búsqueda por embeddings (OpenAI) con fuente, umbral 0.45, TF-IDF de respaldo si la API falla, medidor de costo y caché de vectores; `router.py` híbrido (reglas + LLM validado) y `evaluar_router.py` con 12 casos.
- **Qué falló:** el router acertó 9/12 en su 1.ª versión: trataba las fechas imprecisas como faltantes; al corregir el prompt, "el jueves" sufrió una regresión. Un cliente puntual y uno inexistente devolvían la misma lista vacía. Además, `config_caso.py` quedó commiteado con el orden de la semilla cambiado (21/3/400 en vez de 21/5/300); se detectó al probar las Reglas y se corrigió (Evidencia 5). La API key quedó escrita en `.env.example` (archivo que sí va a git); se detectó antes del commit y se movió a `.env`.
- **Qué aprendí:** una lista vacía no distingue "no hay datos" de "no existe"; validar en la tabla oficial (`clientes`) y devolver un valor, no solo imprimir. TF-IDF solo compara palabras exactas: falla con sinónimos y un puntaje alto no garantiza una respuesta correcta. Los embeddings entienden sinónimos pero no son infalibles, nunca dan 0 y necesitan su propio umbral. Las etiquetas de evaluación son un solucionario que el router no ve; un error puede ser del sistema o del criterio humano; cada cambio se reevalúa con todos los casos para detectar regresiones.
- **Qué decisión cambió:** validar el cliente antes de consultar (D4); usar embeddings en vez de TF-IDF tras compararlos (D6); enriquecer los chunks con el título del documento tras ver fallar la #2 (D7); router híbrido (D8); criterio estricto de fechas tras la evaluación (D9).
- **Evidencia:** EVIDENCIAS.md · Evidencias 3 a 14 (router final 14/14; 26 pruebas pytest).

**Preguntas de razonamiento**
- **¿Por qué una consulta de ventas históricas no debería resolverse con RAG?** Porque los datos están estructurados en tablas: SQL cuenta y filtra con exactitud, mientras que RAG solo encuentra textos parecidos y no sabe contar (la pregunta de entregas tardías obtuvo 0.379 contra un texto de política sin la respuesta).
- **¿Qué ocurre si el router tiene baja confianza?** Si el LLM informa confianza < 0.7, `validar()` envía la solicitud a CLARIFY: se pide aclaración al usuario en vez de adivinar o ejecutar herramientas.
- **¿Cuál es el costo de enviar toda pregunta a todas las herramientas?** Más dinero y más tiempo por pregunta, ineficiencia en preguntas simples (saludos, aclaraciones) y respuestas contradictorias entre fuentes que hacen más difícil decidir.

## Hito 3 · Workflow con estado — ✅ completado

**State del workflow** (pequeño a propósito: va solo lo que un nodo posterior o una bifurcación necesita leer, si es pequeño y no es secreto):

| Campo | Para qué sirve | Quién lo escribe → quién lo lee |
|---|---|---|
| `solicitud` | texto original del cliente | entrada → router |
| `destino` | RAG / SQL / TOOLS / CLARIFY / DIRECT | router → bifurcación tras el router |
| `cliente_id`, `sku`, `cantidad`, `fecha` | datos del pedido | router → validación, Tools y Reglas |
| `dias_transito` | días de envío a la ciudad del cliente | validación → Reglas (fecha mínima y de despacho) |
| `stock`, `libres` | stock y capacidad libre del día de despacho | Tools → Reglas. Son una foto del momento: al reanudar (Hito 4) se vuelven a consultar |
| `decision`, `motivos` | APROBADO / EXCEPCION / RECHAZADO / DATOS_INVALIDOS y por qué | Reglas → bifurcación, supervisor y auditoría |
| `respuesta` | texto final para el usuario | último nodo → salida |

- **Qué se construyó:** `workflow.py` con 6 nodos (enrutar, validar_datos, consultar_estado, evaluar, responder, atender_consulta) y 2 conditional edges (¿es un pedido? · ¿datos válidos?). La excepción todavía termina en `responder`; en el Hito 4 irá al supervisor con `interrupt()`.
- **Evidencia:** EVIDENCIAS.md · Evidencia 15; diagrama en `docs/diagrama_workflow.md`.

**No van al State:** todas las ventas del cliente y el texto de los chunks (grandes y se pueden volver a consultar), la API key (quedaría escrita en disco con el checkpoint), el prompt y la respuesta cruda del LLM, y los vectores de embeddings (muy grandes e innecesarios para los nodos siguientes).
**Preguntas de razonamiento**
- **¿Por qué no basta una cadena de if/else?** Porque el proceso debe poder pausarse a mitad del camino (excepción → supervisor), guardar su estado y continuar horas después con el mismo `id_hilo`; un if/else no puede hacerlo. Además, el grafo permite reintentar solo el paso que falla, deja trazabilidad de cada nodo y se modifica agregando nodos sin reescribir condiciones anidadas.
- **¿Qué información necesita sobrevivir de un nodo a otro?** La solicitud y los datos del pedido (destino, cliente, SKU, cantidad, fecha), lo que producen los nodos intermedios (días de tránsito, stock, capacidad libre) y, sobre todo, la decisión y sus motivos, que leen la bifurcación y el supervisor.
- **¿Qué campo del State sería innecesario o peligroso guardar?** Peligroso: la API key (quedaría escrita en disco con el checkpoint). Innecesario: todas las ventas del cliente, los chunks y los vectores (grandes y se pueden volver a consultar). Riesgoso: `stock` y `libres`, que pueden quedar desactualizados al reanudar.

## Hito 4 · Retry, checkpoint y HITL — ✅ completado

- **Qué se construyó:** nodo `supervisor` con `interrupt()`, checkpoint persistente en SQLite (`data/checkpoints.db`), reanudación con el mismo `id_hilo` desde otro proceso (`iniciar` / `estado` / `reanudar`), nodo `reverificar` que vuelve a consultar el stock al aprobar, y fecha estándar alternativa al rechazar. 8 nodos y 4 conditional edges. `RetryPolicy` solo en `enrutar`, con filtro de errores transitorios (`es_fallo_transitorio`) y simulación de cortes (`--fallos N`).
- **Qué falló:** el router atrapaba todos los errores de OpenAI y devolvía CLARIFY: el retry nunca se habría activado (el error se "tragaba"). Además, la librería `openai` reintentaba por su cuenta, lo que sumado al `RetryPolicy` daba hasta 9 intentos ocultos.
- **Qué aprendí:** el retry solo sirve si el error llega al workflow; un 429 puede ser transitorio (límite de solicitudes) o permanente (sin saldo) y hay que mirar su código.
- **Evidencia:** EVIDENCIAS.md · Evidencias 16 (pausa, estado, aprobación, rechazo) y 17 (retry vs. regla sin retry); 36 pruebas.

**Preguntas de razonamiento**
- **¿Qué error merece retry y cuál no?** Merecen retry los fallos transitorios, donde esperar y repetir puede dar otro resultado: corte de internet, tiempo agotado, servidor caído o límite de solicitudes. No lo merecen la clave inválida, la falta de saldo, una regla de negocio rechazada (el stock seguirá siendo 4) ni un dato inválido (el cliente seguirá sin existir).
- **¿Qué se pierde si no existe checkpoint?** El estado vive solo en memoria: si el programa se cierra mientras espera al supervisor, el pedido pausado desaparece, su respuesta no tiene a dónde llegar, hay que repetir todo (incluido el router, que cuesta) y no queda registro de lo decidido.
- **¿Por qué un side effect antes de `interrupt()` puede ser peligroso?** Porque al reanudar el nodo se ejecuta de nuevo desde la primera línea: un correo se enviaría dos veces; una reserva de capacidad o un cobro de 300 USD se duplicarían.
- **¿Qué pasa si se reanuda con otro `id_hilo`?** Si no existe, no hay nada que reanudar. Si existe pero es otro pedido, se aprueba (y se paga) un despacho que nadie pidió y el pedido real queda pausado indefinidamente: el sistema no puede detectarlo, por eso conviene confirmar el resumen del pedido antes de aplicar la decisión.
## Hito 5 · MCP — 🟡 en curso

- **Qué se construyó:** `mcp_servidor.py` (stdio) con 4 Tools de solo lectura (`consultar_stock`, `consultar_capacidad`, `consultar_transito`, `consultar_fecha_despacho`) y 2 Resources (políticas); `mcp_cliente.py`, cliente puro sin LLM; `agente_mcp.py`, agente que consume el mismo servidor; diagrama antes/después en `docs/diagrama_mcp.md`.
- **Qué falló:** el SDK de MCP había cambiado de versión (2.x): `FastMCP` pasó a llamarse `MCPServer` y los atributos de las respuestas usan `snake_case` (`is_error`).
- **Qué aprendí:** con stdio la salida estándar transporta el protocolo, así que el servidor no puede imprimir en ella; lo que no se publica en el servidor no existe para los clientes (mínimo privilegio).
- **Qué decisión cambió:** se agregó `consultar_fecha_despacho` para que el agente no calcule fechas con el LLM (D13).
- **Evidencia:** EVIDENCIAS.md · Evidencias 18 (cliente puro) y 19 (agente); 43 pruebas.
- **Pendiente:** preguntas de razonamiento.
## Hito 6 · Integración y reflexión — ⚪ pendiente
