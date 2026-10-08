# HITOS · LOG-009 · Logística · Semilla 9911

## Hito 1 · Separar responsabilidades — 🟡 en curso

- **Qué se construyó:** proyecto con uv (Python 3.12) y `config_caso.py`: la semilla 9911 genera capacidad diaria (21), ventana de entrega (5 días) y costo extraordinario (300 USD).
- **Qué falló:** ejecutar desde una carpeta equivocada (`program not found`).
- **Qué aprendí:** la semilla genera una secuencia pseudoaleatoria fija; cambiar el orden de las llamadas cambia los valores.
- **Qué decisión cambió:** la ciudad de destino se incluye en el cálculo del plazo (D2).
- **Evidencia:** EVIDENCIAS.md · Evidencia 1.
- **Datos:** 6 CSV en `data/` (clientes, ciudades, productos, inventario, ventas, despachos programados).
- **Pendiente:** carga a SQLite, 6–10 solicitudes, tabla "consulta → capacidad → justificación".

## Hito 2 · Router + RAG + SQL + Tools — ⚪ pendiente
## Hito 3 · Workflow con estado — ⚪ pendiente
## Hito 4 · Retry, checkpoint y HITL — ⚪ pendiente
## Hito 5 · MCP — ⚪ pendiente
## Hito 6 · Integración y reflexión — ⚪ pendiente
