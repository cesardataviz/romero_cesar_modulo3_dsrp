# Limitaciones y riesgos · LOG-009

Limitaciones observadas durante el desarrollo, con su origen (decisión o evidencia).

## Las tres más importantes

| # | Limitación | Por qué importa |
|---|---|---|
| **3** | **Aprobar no reserva nada**: al confirmar un pedido, ni el stock baja ni la capacidad del día se ocupa, porque ningún componente escribe en la base. | Dos clientes pueden recibir confirmación por las mismas unidades (hay 18 EDGE-ORIN: se aprueban 12 para C-1003 y luego 10 para C-1006, porque el stock sigue en 18). Uno no recibirá su pedido. |
| **13** | **Mensaje engañoso si el LLM falla de forma permanente**: con clave inválida o sin saldo, el cliente recibe "Necesito más información". | El cliente cree que su pregunta está mal y la reformula; el problema real es el servicio y nadie se entera de la caída. |
| **18** | **Supervisor sin autenticación**: cualquiera que ejecute `reanudar` puede autorizar un despacho extraordinario, y el supervisor puede equivocarse de `id_hilo`. | Se puede autorizar un gasto de 300 USD sin control, o aprobar el pedido equivocado (D11). |

**Mayor riesgo del diseño actual: la #3.** Ocurre en el camino normal (no necesita ningún fallo), es silencioso (cada respuesta por separado es correcta) y su costo es alto (promesas de entrega imposibles de cumplir).

## Lista completa

### Reglas y datos
| # | Limitación | Origen |
|---|---|---|
| 1 | No conoce feriados: un martes feriado se trata como día hábil. | D5 |
| 2 | "Hoy" es fijo (2026-10-12): no usa la fecha real. | D3 |
| 3 | Aprobar no reserva stock ni capacidad. | D1, D14 |
| 4 | "Cuanto antes" propone la fecha mínima aunque no tenga capacidad, en lugar de buscar el siguiente día con cupo. | Evidencia 15 |
| 5 | No intenta despachar antes cuando el día de despacho no tiene capacidad: va directo al supervisor. | Propuesta propia (Hito 5) |
| 6 | Las ciudades no registradas (Iquitos) quedan sin fecha posible. | D2 |
| 7 | No distingue un cliente dado de baja de uno activo. | D4 |

### Router y LLM
| # | Limitación | Origen |
|---|---|---|
| 8 | La confianza del router la declara el propio LLM; no es una probabilidad calibrada. | D12 |
| 9 | Las reglas por palabra clave son ciegas al contexto: "¿Cuál es la política de entregas tardías?" va a SQL. | D8 |
| 10 | El criterio estricto de fechas obliga al cliente a responder más preguntas. | D9 |
| 11 | Solo 14 casos de evaluación; las confianzas varían entre ejecuciones. | Evidencias 12 y 13 |
| 12 | La consulta SQL no resuelve nombres de clientes ("Agroindustrial del Norte"): pide el código. | Evidencia 20 |
| 13 | Ante un fallo permanente del LLM, el mensaje al cliente es engañoso. | Prueba del Hito 6 |

### RAG
| # | Limitación | Origen |
|---|---|---|
| 14 | "Aprobación" ganó por un margen de 0,019: una reformulación puede invertir el resultado. | D7 |
| 15 | El umbral 0,45 se calibró con solo 5 preguntas. | Evidencias 8 y 9 |
| 16 | El respaldo TF-IDF falla con sinónimos: si la API cae, "¿quién autoriza…?" responde con la sección de Costo. | Evidencias 7 y 20 |
| 17 | Devuelve el texto literal de la política, sin redactar una respuesta a la medida. | Hito 2 |

### HITL, MCP y operación
| # | Limitación | Origen |
|---|---|---|
| 18 | Supervisor sin autenticación; puede equivocarse de `id_hilo`. | D11 |
| 19 | Las pausas no expiran: un pedido puede quedar esperando indefinidamente. | D11 |
| 20 | El servidor MCP no pide identificación. | D13 |
| 21 | Dos caminos al mismo código (workflow y MCP) pueden divergir si se agrega lógica en uno solo. | D14 |
| 22 | Un solo proveedor de LLM: si OpenAI cae, el router y el agente se detienen. | D6, D12 |
| 23 | Las pruebas usan la base real: dos ejecuciones simultáneas chocan. | Hito 5 |
| 24 | La app no está publicada en la nube: Hugging Face bloqueó el hardware gratuito (CPU basic) de la cuenta. Aun publicada allí, no habría almacenamiento persistente y los expedientes pausados se perderían al reiniciar. | D15 |
| 25 | El cliente no recibe un aviso automático cuando el supervisor decide: debe consultar su expediente en *Seguimiento de expediente*. | Prueba de la interfaz |

## Mejoras propuestas

- **Despachar antes:** si el día de despacho no tiene capacidad, buscar un día hábil anterior con cupo (no antes de hoy) antes de escalar al supervisor.
- **Invitar a registrarse:** si quien escribe no es cliente registrado, ofrecerle registrarse en lugar de solo rechazar el pedido.
- **Aviso automático al cliente:** notificar en el chat (o por correo) cuando el supervisor aprueba o rechaza su expediente.
- **Reservar al aprobar:** registrar la reserva de stock y capacidad (idempotente) para resolver la limitación #3.
