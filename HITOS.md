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

## Hito 3 · Workflow con estado — ⚪ pendiente
## Hito 4 · Retry, checkpoint y HITL — ⚪ pendiente
## Hito 5 · MCP — ⚪ pendiente
## Hito 6 · Integración y reflexión — ⚪ pendiente
