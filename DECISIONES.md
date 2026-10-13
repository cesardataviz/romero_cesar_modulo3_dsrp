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
- **Riesgo:** sin internet, con la API caída o sin saldo, el sistema se caería con un error y no respondería ninguna pregunta de políticas.
- **Mitigación:** si la API falla, `responder()` usa TF-IDF como respaldo automático (menos preciso, pero local).
- **En producción:** un plan B real: proveedor alternativo de embeddings o un modelo local, reintentos solo para fallos transitorios y alertas cuando se active el respaldo.

## D7 · Enriquecer cada chunk con el título de su documento

- **Problema:** con embeddings, "¿Quién debe aprobar un despacho extraordinario?" devolvía "Cuándo aplica" en vez de "Aprobación".
- **Alternativas:** devolver los 2 mejores chunks · enriquecer el texto de los chunks · aceptarlo como limitación.
- **Decisión:** anteponer el título del documento a cada chunk ("Política de despacho extraordinario — Aprobación. ...").
- **Trade-off:** corrige el caso sin agrandar la respuesta; a cambio, el margen es estrecho (0.650 vs. 0.631).
- **Riesgo:** el margen es de solo 0.019: si un cliente reformula la pregunta, "Cuándo aplica" podría volver a ganar y el sistema respondería con seguridad y equivocado, sin que nadie lo note.
- **En producción:** con cientos de documentos no bastaría el título: se enriquecerían los chunks con metadatos (palabras clave, términos relacionados) y cada cambio se validaría contra un conjunto fijo de preguntas de evaluación para comprobar que no empeora otras.

## D8 · Router híbrido: reglas + LLM validado

- **Problema:** decidir a qué capacidad va cada solicitud (RAG, SQL, TOOLS, CLARIFY, DIRECT) y extraer cliente, SKU, cantidad y fecha.
- **Alternativas:** determinístico (solo reglas) · modelo (solo LLM) · híbrido.
- **Decisión:** híbrido. Reglas para lo obvio (saludos, palabras de historial o de política); LLM (`gpt-6-luna`, salida estructurada) para el resto; si la confianza es baja o faltan datos, CLARIFY; si el LLM falla, CLARIFY.
- **Trade-off:** barato y predecible donde se puede, flexible donde se necesita; a cambio, más piezas que mantener y explicar.
- **Riesgo:** las reglas por palabra clave son ciegas al contexto y se evalúan en orden: "¿Cuál es la política de entregas tardías?" va a SQL (la regla de historial se revisa antes que la de política), con confianza 1.0 y sin pasar por la validación del LLM.
- **En producción:** reglas solo para patrones inequívocos, conflictos (dos reglas a la vez) derivados al LLM, y evaluación continua con un conjunto más grande de casos reales.

## D9 · Criterio para fechas imprecisas en el router

- **Problema:** la 1.ª evaluación del router dio 9/12; los 3 errores eran fechas imprecisas ("el 22", "lo antes posible", "la próxima semana") enviadas a CLARIFY.
- **Alternativas:** enviar toda fecha imprecisa a CLARIFY · tratar "lo antes posible" como pedido sin fecha · interpretar todo automáticamente.
- **Decisión (criterio estricto):** solo se aceptan fechas completas (día + mes, o día de la semana + número, p. ej. "el viernes 23"). "El jueves", "el 22", "la próxima semana", "a fin de mes" o "pronto" → CLARIFY. "Lo antes posible" / "cuanto antes" → TOOLS sin fecha: el sistema propone la fecha más cercana con `fecha_minima_entrega`. Se corrigieron las etiquetas de los casos #1, #2 y #8.
- **Trade-off:** se evita prometer una fecha mal interpretada; a cambio, el cliente debe responder más preguntas, y el criterio vive en el prompt y depende de que el LLM lo siga. Se descartó interpretar "el jueves" o "el 22" como su próxima ocurrencia.
- **Riesgo:** más preguntas al cliente: quien escribe "el jueves" esperando rapidez recibe una aclaración extra; repetido, el sistema se vuelve lento y molesto. Además, el criterio vive en el prompt y el LLM podría aplicarlo de forma inconsistente.
- **En producción:** proponer la fecha interpretada para que el cliente la confirme con un clic ("¿Te refieres al jueves 15?"), en lugar de una pregunta abierta.

## D10 · State pequeño para el workflow

- **Problema:** decidir qué datos viajan entre los nodos del grafo y se guardarán en cada checkpoint (Hito 4).
- **Alternativas:** guardar todo lo disponible (ventas, chunks, prompts, vectores) · guardar solo lo que un nodo posterior o una bifurcación necesita.
- **Decisión:** 12 campos pequeños (solicitud, destino, datos del pedido, tránsito, stock, libres, decisión, motivos, respuesta); nada grande, nada secreto, nada que se pueda volver a consultar.
- **Trade-off:** checkpoints livianos y sin secretos; a cambio, algunos datos deben volver a consultarse cuando hagan falta.
- **Riesgo:** `stock` y `libres` son una foto del momento: si el flujo se pausa y el supervisor responde horas después, podrían estar desactualizados y confirmarse una entrega imposible.
- **En producción:** volver a consultar stock y capacidad al reanudar, antes de confirmar; y registrar en el State solo identificadores para auditar, no datos sensibles.

## D11 · Human-in-the-Loop con checkpoint persistente y reverificación

- **Problema:** una excepción (fecha anterior a la mínima o capacidad insuficiente) no puede resolverla el sistema: la decide el Supervisor de logística, que puede responder horas después.
- **Alternativas:** responder "requiere aprobación" y terminar · pausar con `interrupt()` en memoria · pausar con checkpoint persistente en SQLite.
- **Decisión:** `interrupt()` en el nodo `supervisor` con checkpoint en `data/checkpoints.db`; se reanuda con el mismo `id_hilo` desde otro proceso. Sin side effects antes de `interrupt()`. Si aprueba, se vuelve a consultar el stock antes de confirmar; si rechaza, se ofrece la fecha estándar más cercana con capacidad. Una respuesta no válida del supervisor se trata como rechazo.
- **Trade-off:** el proceso sobrevive a reinicios y queda auditable; a cambio, hay un archivo de estado más que administrar y un nodo que se re-ejecuta al reanudar.
- **Riesgo:** el sistema acepta cualquier `id_hilo` válido sin confirmar a qué pedido corresponde: si el supervisor se equivoca de expediente, se aprueba (y se paga) un despacho que nadie pidió y el pedido real queda pausado, con el cliente insatisfecho. Además, un pedido puede quedar pausado indefinidamente si el supervisor nunca responde.
- **En producción:** mostrar el resumen del pedido y pedir confirmación antes de aplicar la decisión; autenticar quién puede aprobar; plazo máximo de espera con recordatorio o escalamiento; notificaciones enviadas después de la pausa y de forma idempotente; registro de auditoría de cada aprobación.

## D12 · Retry solo para fallos transitorios del LLM

- **Problema:** el router atrapaba todos los errores de OpenAI y devolvía CLARIFY, así que un corte de red momentáneo nunca se reintentaba ("se tragaba" el error).
- **Alternativas:** retry en todo el grafo · retry de la librería `openai` (2 internos) · `RetryPolicy` solo en el nodo `enrutar` con un filtro de errores.
- **Decisión:** `RetryPolicy(max_attempts=3)` solo en `enrutar`, con `es_fallo_transitorio`: se reintentan corte de red, tiempo agotado, servidor caído y límite de solicitudes; no se reintentan clave inválida ni falta de saldo (`insufficient_quota`), que van a CLARIFY. La librería no reintenta (`max_retries=0`) para tener una sola capa de reintentos. Las reglas de negocio y los datos inválidos nunca se reintentan. Para la demo, `--fallos N` provoca N cortes simulados.
- **Trade-off:** se recupera solo de fallos momentáneos; a cambio, la solicitud tarda más (esperas de 0,5 s y 1 s) y hay que mantener la clasificación de errores.
- **Riesgo:** si OpenAI sigue caído tras los 3 intentos, el cliente espera casi 2 s y recibe un "intenta más tarde": puede irse y se pierde el pedido. Además, si muchas solicitudes reintentan a la vez contra un servidor saturado, lo empeoran (las esperas crecientes con variación aleatoria lo mitigan).
- **En producción:** modelo o proveedor de respaldo cuando el principal no responde; para el router, un modelo de decisiones estructuradas como Jev (TypeSafe AI), que devuelve probabilidades por opción en vez de una confianza autodeclarada (evaluándolo antes con los 14 casos); reintentos diferidos del mismo `id_hilo` desde el checkpoint cuando el servicio vuelva, sin que el cliente repita su solicitud; y alertas si la caída se prolonga.

## D13 · Servidor MCP con mínimo privilegio

- **Problema:** otras aplicaciones (portal, chatbot de otro equipo, Claude Desktop) necesitan consultar stock, capacidad y tránsito; hoy tendrían que importar el código Python y acceder a toda la base de datos.
- **Alternativas:** exponer todo (incluido `ejecutar_sql`, aprobar despachos, actualizar stock, historial) · exponer la evaluación completa del pedido · exponer solo consultas de lectura.
- **Decisión:** servidor MCP stdio con 4 Tools de solo lectura (`consultar_stock`, `consultar_capacidad`, `consultar_transito`, `consultar_fecha_despacho`) y 2 Resources (las dos políticas). `consultar_fecha_despacho` se agregó para que el agente no calcule fechas: un LLM podría restar mal los días hábiles con total seguridad; el cálculo lo hace Python (`reglas.fecha_despacho`). No se exponen SQL libre, escritura de stock, aprobación de despachos (HITL), historial de ventas ni la evaluación de reglas. `consultar_capacidad` indica si el día es hábil, porque los consumidores no tienen acceso a la regla D5.
- **Trade-off:** cualquier cliente MCP, en cualquier lenguaje, usa las capacidades sin conocer el código ni la base; a cambio, las otras aplicaciones deben combinar las consultas por su cuenta para saber si una entrega es viable.
- **Riesgo:** el servidor no pide identificación: cualquier programa que pueda iniciarlo podría extraer información de stock y capacidad o saturarlo con consultas hasta hacerlo caer. Con stdio el riesgo es local (lo inicia un programa en la misma máquina); sería crítico si se publicara en red.
- **En producción:** autenticación (saber quién consulta y desde dónde, solo clientes y sistemas registrados), autorización por herramienta (scopes: no todos ven lo mismo), límite de consultas por cliente y registro de cada llamada.
