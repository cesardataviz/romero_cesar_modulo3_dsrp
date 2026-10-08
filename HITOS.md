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

## Hito 2 · Router + RAG + SQL + Tools — 🟡 en curso

- **Qué se construyó:** `consultas_sql.py` con 3 consultas parametrizadas (entregas tardías, historial, cumplimiento) y `cliente_existe`; `tools.py` con 4 Tools semánticas (cliente, stock, capacidad, tránsito).
- **Qué falló:** un cliente puntual y uno inexistente devolvían la misma lista vacía.
- **Qué aprendí:** una lista vacía no distingue "no hay datos" de "no existe"; validar en la tabla oficial (`clientes`) y devolver un valor, no solo imprimir.
- **Qué decisión cambió:** validar el cliente antes de consultar (D4).
- **Evidencia:** EVIDENCIAS.md · Evidencias 3 y 4.
- **Pendiente:** Reglas, RAG, Router y sus pruebas.

## Hito 3 · Workflow con estado — ⚪ pendiente
## Hito 4 · Retry, checkpoint y HITL — ⚪ pendiente
## Hito 5 · MCP — ⚪ pendiente
## Hito 6 · Integración y reflexión — ⚪ pendiente
