# Clasificación de solicitudes · LOG-009

Evidencia del Hito 1: qué capacidad debería resolver cada solicitud y por qué.

**Criterios:** SQL = qué pasó (historial) · Tool = qué hay ahora (estado actual) · RAG = qué dice un documento · Regla = decisión objetiva con datos · Aclarar = falta información · Directa = no requiere consultar nada.

| # | Solicitud | Capacidad esperada | Justificación |
|---|---|---|---|
| 1 | "¿Pueden entregar 12 EDGE-ORIN a C-1003 el jueves?" | Tool + Regla | Stock y capacidad libre son datos actuales (Tool); si la fecha cabe en plazo y capacidad es una decisión objetiva (Regla). Caso base: genera excepción |
| 2 | "¿Pueden despachar 5 PLC-S7M a C-1004 en Arequipa para el 22?" | Tool + Regla | Stock y capacidad actuales (Tool); plazo = ventana + días de tránsito de Arequipa (Regla). Ruta normal sin excepción |
| 3 | "C-1008 necesita 6 CAM-GIGE5 para el viernes 23." | Tool + Regla | Stock actual (Tool); pide 6 y hay 4 → stock insuficiente (Regla) |
| 4 | "¿Cuántas entregas tardías ha tenido Agroindustrial del Norte?" | SQL | Pregunta sobre el pasado: compara fecha prometida vs. entregada en el historial de ventas |
| 5 | "¿Cuál es la política para un despacho extraordinario?" | RAG | La respuesta está en un documento de política, no en una tabla de datos |
| 6 | "¿Cuál es el plazo estándar de entrega a Piura?" | Ambigua (RAG o Regla) | Puede leerse como política (RAG) o como cálculo ventana + tránsito (Regla). Candidata a error del router |
| 7 | "Envíen 3 EDGE-NANO a C-1007 en Iquitos lo antes posible." | Tool → Aclarar | La Tool encuentra al cliente, pero Iquitos no está en la tabla de ciudades: no se compromete fecha (D2) |
| 8 | "C-1099 quiere 10 SENS-PROX para la próxima semana." | Tool → Aclarar | La Tool detecta que el cliente no existe; se pide aclaración en lugar de inventar |
| 9 | "Necesito unos equipos para pronto." | Aclarar | Faltan producto, cantidad y fecha; no se puede actuar |
| 10 | "Hola, ¿qué puedes hacer por mí?" | Directa | Es clara y no necesita datos: la mejor acción es no ejecutar ninguna herramienta |
