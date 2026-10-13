---
title: AndesSupply Despachos LOG-009
emoji: 🚚
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 6.30.0
python_version: "3.12"
app_file: app.py
pinned: false
short_description: Agente de despachos B2B con aprobación del supervisor
---

# AndesSupply · Asistente de despachos (LOG-009)

Agente que decide si AndesSupply puede comprometer una fecha de entrega. Las reglas de negocio (plazos, capacidad, stock) se calculan en Python; el LLM solo interpreta el lenguaje. Las excepciones se pausan hasta que el Supervisor de logística las aprueba o rechaza.

- **Cliente / Vendedor:** chat con el agente.
- **Supervisor de logística:** expedientes pausados, con su resumen y botones Aprobar/Rechazar.

Acceso protegido con usuario y contraseña. Código fuente y documentación en el repositorio de GitHub del proyecto.
