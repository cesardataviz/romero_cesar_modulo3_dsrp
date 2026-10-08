# DECISIONES · LOG-009 · Logística · Semilla 9911

## D1 · Formato de los datos

- **Problema:** necesito datos que pueda editar fácilmente y consultar con SQL parametrizado.
- **Alternativas:** solo CSV · solo SQLite · CSV como fuente + carga a SQLite.
- **Decisión:** CSV para editar y SQLite para las consultas SQL.
- **Trade-off:** gano facilidad de edición y SQL real; a cambio, hay un paso extra de carga y dos copias de los datos.
- **Riesgo:** si se edita el CSV y no se actualiza SQLite, el agente daría información desactualizada, por ejemplo confirmar stock que no existe.
- **Mitigación:** regenerar SQLite desde los CSV automáticamente al iniciar el sistema.
- **En producción:** el stock y los despachos vendrían del ERP (p. ej. SAP) y los clientes del CRM, consultados en tiempo real; una sola fuente de verdad.

## D2 · La ciudad de destino afecta el plazo de entrega

- **Problema:** un mismo plazo para todos los destinos no es realista (Lima vs. Arequipa).
- **Alternativas:** plazo único para todos · plazo según ciudad de destino.
- **Decisión:** plazo según ciudad: `plazo = ventana_entrega_dias + dias_transito(ciudad)`.
- **Trade-off:** más realismo; a cambio, una tabla más que mantener.
- **Riesgo:** si la ciudad no está en la tabla, el sistema podría fallar o prometer una fecha imposible y perder la confianza del cliente.
- **Mitigación:** ciudad no registrada → no comprometer fecha; pedir aclaración o derivar al supervisor.
- **En producción:** los días de tránsito varían (feriados, clima, transportista); vendrían actualizados del transportista o del ERP.

## D3 · Fecha de referencia fija para el escenario

- **Problema:** si el sistema usa la fecha real de hoy, los resultados cambian cada día y la demo deja de ser reproducible.
- **Alternativas:** fecha real del sistema · fecha de referencia fija.
- **Decisión:** "hoy" del escenario = lunes 2026-10-12.
- **Trade-off:** reproducible; a cambio, no refleja el día real.
- **Riesgo:** si el sistema se usara como real con la fecha fija, calcularía plazos desde un día equivocado y prometería fechas incorrectas.
- **En producción:** se usaría la fecha actual; la fecha sería configurable (fija solo para pruebas y demo).

## D4 · Validar el cliente antes de interpretar una consulta

- **Problema:** un cliente puntual y uno inexistente devuelven el mismo resultado vacío; el agente podría decir "no tiene retrasos" de un cliente que no existe.
- **Alternativas:** buscar al cliente en `ventas` · buscar en `clientes` · solo imprimir un mensaje.
- **Decisión:** función `cliente_existe` que busca en `clientes` y devuelve True/False.
- **Trade-off:** una consulta extra por solicitud; a cambio, respuestas correctas.
- **Riesgo:** "existe" no significa "está habilitado": un cliente dado de baja seguiría en la tabla y el agente podría comprometerle una entrega. A gran escala, la consulta extra suma carga.
- **En producción:** el cliente y su estado (activo, bloqueado, de baja) se validarían en el CRM/ERP en tiempo real.
