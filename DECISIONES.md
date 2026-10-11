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
- **Decisión:** "hoy" del escenario = lunes 2026-10-12 (`FECHA_REFERENCIA`): primer día de la agenda de despachos, posterior a todo el historial de ventas.
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

## D5 · Los días no hábiles los decide una Regla, no la Tool

- **Problema:** una fecha sin despachos registrados (p. ej. sábado) aparece con capacidad libre completa; el sistema podría comprometer una entrega que nunca saldrá.
- **Alternativas:** que la Tool devuelva 0 en fines de semana · que una Regla valide los días hábiles.
- **Decisión:** la Tool solo informa datos; la Regla decide que sábados y domingos no se despacha.
- **Trade-off:** separación clara de responsabilidades; a cambio, la Tool sola no basta: siempre debe pasar por la Regla.
- **Riesgo:** la regla no conoce feriados: un feriado entre semana (p. ej. martes 8 de diciembre) se trataría como hábil y se aprobaría una entrega que no puede salir.
- **En producción:** una tabla de calendario con los feriados oficiales (gob.pe), cargada periódicamente en el ERP; la regla consultaría esa tabla.

## D6 · Búsqueda en políticas (RAG): embeddings con OpenAI, TF-IDF como línea base

- **Problema:** encontrar el fragmento de política que responde una pregunta, aunque use palabras distintas a las del documento.
- **Alternativas:** TF-IDF (por palabras, local) · embeddings locales · embeddings por API (Voyage AI u OpenAI).
- **Decisión:** embeddings por API con OpenAI (`text-embedding-3-small`), porque ya tengo cuenta; TF-IDF se implementa también como línea base para comparar.
- **Trade-off:** entiende sinónimos ("urgente" ≈ "extraordinario") y no requiere descargas pesadas; a cambio, depende de internet y de una API key.
- **Riesgo:** (pendiente)
- **En producción:** (pendiente)

## D7 · Enriquecer cada chunk con el título de su documento

- **Problema:** con embeddings, "¿Quién debe aprobar un despacho extraordinario?" devolvía "Cuándo aplica" en vez de "Aprobación".
- **Alternativas:** devolver los 2 mejores chunks · enriquecer el texto de los chunks · aceptarlo como limitación.
- **Decisión:** anteponer el título del documento a cada chunk ("Política de despacho extraordinario — Aprobación. ...").
- **Trade-off:** corrige el caso sin agrandar la respuesta; a cambio, el margen es estrecho (0.650 vs. 0.631).
- **Riesgo:** ¿qué error comete el sistema? La #2 ganó por solo 0.019. ¿Qué podría pasar si un cliente pregunta lo mismo con otras palabras?. Probablemente el sistema si pueda seguir reconociendo los sinónimos usando Embeddings y por ende, entendiendo el contexto de la pregunta para acercar la respuesta más acertada.
- **En producción:** con cientos de documentos en vez de 2, ¿bastaría con agregar el título? Pista: piensa en cómo comprobarías que un cambio no empeora otras preguntas. Considero, que no es factible solo añadir el título, sería bueno añadir un subtítulo o un párrafo. Lo que debería hacerse es agregar palabras clave y palabras relacionadas que podrían acercarse a las preguntas.
