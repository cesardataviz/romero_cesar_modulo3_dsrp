# EVIDENCIAS · LOG-009 · Logística · Semilla 9911

Registro de ejecuciones reales que demuestran que cada parte funciona.

---

## Hito 1 · Evidencia 1: reproducibilidad de la semilla

**Fecha:** 2026-10-07
**Qué demuestra:** con la misma SEMILLA el escenario es idéntico (regla mínima del enunciado, §5).
**Comando:**

```bash
uv run config_caso.py
```

**Ejecución 1:**

```
CASO_ID=LOG-009, SEMILLA=9911, VARIANTE=Logística, capacidad_diaria=21, ventana_entrega_dias=5, costo_extraordinario=300
capacidad_diaria=21 unidades/día
ventana_entrega_dias=5 días hábiles
costo_extraordinario=300 USD
```

**Ejecución 2:**

```
CASO_ID=LOG-009, SEMILLA=9911, VARIANTE=Logística, capacidad_diaria=21, ventana_entrega_dias=5, costo_extraordinario=300
capacidad_diaria=21 unidades/día
ventana_entrega_dias=5 días hábiles
costo_extraordinario=300 USD
```

**Resultado:** ✅ Ambas ejecuciones producen los mismos valores.
**Por qué ocurre:** 
Los números de random no son realmente aleatorios: son pseudoaleatorios. Salen de una fórmula matemática. La semilla es el punto de partida de esa fórmula. Cada vez que se llama a rng.randint(...) o rng.choice(...), el generador avanza un paso en la secuencia. Mismo punto de partida y mismos pasos dan el mismo resultado.

**¿Qué pasaría con los valores si cambio el orden de las tres líneas rng...?**
Los números cambian, porque cambio la manera en que las variables recibieron cada número. Por eso, para buenas prácticas se sugiere poder añadir al final un nuevo parámetro, para que no se altere el escenario.

---

## Hito 1 · Evidencia 2: carga CSV → SQLite

**Qué demuestra:** la base se reconstruye desde los CSV en cada ejecución (mitigación de D1).
**Comando:** `uv run cargar_datos.py`

```text
Se cargaron 8 filas en la tabla clientes.
Se cargaron 6 filas en la tabla ciudades.
Se cargaron 7 filas en la tabla productos.
Se cargaron 7 filas en la tabla inventario.
Se cargaron 15 filas en la tabla ventas.
Se cargaron 10 filas en la tabla despachos_programados.
Base reconstruida en andessupply.db
```

**Resultado:** ✅ 6 tablas cargadas. La base `.db` no se versiona en git (es un archivo generado).


---

## Hito 2 · Evidencia 3: consultas SQL parametrizadas

**Qué demuestra:** 3 consultas SQL sobre el historial y validación de cliente inexistente.
**Comando:** `uv run consultas_sql.py`

```text
1) Entregas tardías de C-1002:
   {'venta_id': 'V-0005', 'sku': 'EDGE-NANO', 'cantidad': 10, 'fecha_prometida': '2026-08-12', 'fecha_entregada': '2026-08-18', 'dias_retraso': 6}
   {'venta_id': 'V-0012', 'sku': 'SENS-PROX', 'cantidad': 120, 'fecha_prometida': '2026-09-18', 'fecha_entregada': '2026-09-25', 'dias_retraso': 7}
2) Historial de C-1003 desde 2026-07-12:
   {'venta_id': 'V-0002', 'fecha_prometida': '2026-07-22', 'sku': 'CAM-GIGE5', 'producto': 'Camara industrial GigE 5MP', 'cantidad': 4}
   {'venta_id': 'V-0009', 'fecha_prometida': '2026-09-02', 'sku': 'EDGE-ORIN', 'producto': 'Modulo edge computing Orin', 'cantidad': 10}
   {'venta_id': 'V-0015', 'fecha_prometida': '2026-10-01', 'sku': 'LENS-12MM', 'producto': 'Lente industrial 12 mm', 'cantidad': 12}
3) Cumplimiento de C-1002: {'total': 2, 'a_tiempo': 0}
4) Entregas tardías de C-1099 (no existe): []
5) Entregas tardías de C-1001: []
6) C-1001: existe, cumplimiento {'total': 3, 'a_tiempo': 3}
6) C-1099: cliente no existe
```

**Resultado:** ✅ Las 3 consultas responden. Un cliente puntual (C-1001) y uno inexistente (C-1099) devuelven la misma lista vacía; `cliente_existe` los distingue.


---

## Hito 2 · Evidencia 4: Tools semánticas

**Qué demuestra:** 4 Tools que consultan el estado actual y manejan cliente, SKU y ciudad inexistentes.
**Comando:** `uv run tools.py`

```text
1) Cliente C-1003: {'ok': True, 'cliente_id': 'C-1003', 'nombre': 'Textil Lima Industrial SAC', 'ciudad': 'Lima', 'tipo': 'prioritario'}
2) Cliente C-1099: {'ok': False, 'motivo': 'El cliente C-1099 no existe'}
3) Stock EDGE-ORIN: {'ok': True, 'sku': 'EDGE-ORIN', 'nombre': 'Modulo edge computing Orin', 'stock_disponible': 18}
4) Stock DRONE-X1: {'ok': False, 'motivo': 'El SKU DRONE-X1 no existe'}
5) Capacidad jueves 2026-10-15: {'ok': True, 'fecha': '2026-10-15', 'capacidad_diaria': 21, 'comprometidas': 12, 'libres': 9}
6) Tránsito a Arequipa: {'ok': True, 'ciudad': 'Arequipa', 'dias_transito': 2}
7) Tránsito a Iquitos: {'ok': False, 'motivo': 'La ciudad Iquitos no tiene tránsito registrado'}
```

**Resultado:** ✅ Todas las Tools responden con el mismo formato (`ok` + datos o `motivo`); los casos inexistentes se informan sin ambigüedad.


---

## Hito 2 · Evidencia 5: error detectado y corregido (orden de la semilla)

**Qué pasó:** después del experimento del orden, `config_caso.py` quedó guardado con el orden cambiado (capacidad → costo → ventana) y entró así al commit `88bbb4b`. El código producía 21 / 3 / 400, mientras la Evidencia 1 y los `.md` decían 21 / 5 / 300.
**Cómo se detectó:** al probar las Reglas, la fecha mínima y el costo no coincidían con lo esperado.
**Corrección:** se restauró el orden original (capacidad → ventana → costo) en el commit `b3556e8`.

```text
CASO_ID=LOG-009, SEMILLA=9911, VARIANTE=Logística, capacidad_diaria=21, ventana_entrega_dias=5, costo_extraordinario=300
capacidad_diaria=21 unidades/día
ventana_entrega_dias=5 días hábiles
costo_extraordinario=300 USD
```

**Resultado:** ✅ El escenario vuelve a coincidir con la Evidencia 1.


---

## Hito 2 · Evidencia 6: Reglas de negocio

**Qué demuestra:** decisiones objetivas en Python puro: APROBADO, EXCEPCION (requiere supervisor) y RECHAZADO.
**Comando:** `uv run reglas.py`

```text
Fecha mínima Lima (0 días tránsito): 2026-10-19
Fecha mínima Arequipa (2 días): 2026-10-21
1) C-1003 · 12 EDGE-ORIN · jueves 15 · Lima: {'decision': 'EXCEPCION', 'motivos': ['Fecha pedida 2026-10-15 es anterior a la mínima 2026-10-19', 'Capacidad insuficiente: pide 12, quedan 9 libres'], 'requiere': 'Supervisor logística', 'costo_extraordinario': 300}
2) C-1004 · 5 PLC-S7M · 22 · Arequipa (despacho el 2026-10-20 ): {'decision': 'APROBADO', 'motivos': [], 'fecha_entrega': '2026-10-22'}
3) C-1008 · 6 CAM-GIGE5 · viernes 23: {'decision': 'RECHAZADO', 'motivos': ['Stock insuficiente: pide 6, hay 4']}
4) Entrega un sábado 17: {'decision': 'RECHAZADO', 'motivos': ['2026-10-17 no es día hábil (D5)']}
```

**Resultado:** ✅ El caso base genera EXCEPCION con dos motivos; el stock insuficiente y el sábado se RECHAZAN (no tiene sentido pedir aprobación ni reintentar).


---

## Hito 2 · Evidencia 7: RAG con TF-IDF (línea base)

**Qué demuestra:** chunking por sección, respuesta con fuente, un caso que no usa RAG y los límites de la búsqueda por palabras.
**Comando:** `uv run rag.py`

```text
> ¿Cuál es la política para un despacho extraordinario?
  puntaje=0.24 · politica_despacho_extraordinario.md § Cuándo aplica
> ¿Quién debe aprobar un despacho extraordinario?
  puntaje=0.318 · politica_despacho_extraordinario.md § Cuándo aplica
> ¿Despachan los sábados?
  puntaje=0.277 · politica_despacho.md § Días y horario de despacho
> ¿Quién autoriza un envío urgente?
  puntaje=0.242 · politica_despacho_extraordinario.md § Costo
> ¿Cuántas entregas tardías tuvo C-1002?
  puntaje=0.0 · sin fuente → Las políticas no cubren esta pregunta.
```

**Resultado:** 3/5 correctas. Falla #2 ("aprobar" ≠ "aprobación") y #4 (sinónimos "autoriza", "urgente"); la #4 responde mal con un puntaje sobre el umbral. La #5 se descarta correctamente (no es pregunta documental). Predije ambos errores antes de ejecutar.


---

## Hito 2 · Evidencia 8: TF-IDF vs. embeddings (OpenAI `text-embedding-3-small`)

**Qué demuestra:** por qué se eligen embeddings y por qué necesitan un umbral propio.
**Comando:** `uv run rag.py`

```text
> ¿Cuál es la política para un despacho extraordinario?
  TF-IDF     0.240 · politica_despacho_extraordinario.md § Cuándo aplica
  Embeddings 0.693 · politica_despacho_extraordinario.md § Cuándo aplica
> ¿Quién debe aprobar un despacho extraordinario?
  TF-IDF     0.318 · politica_despacho_extraordinario.md § Cuándo aplica
  Embeddings 0.611 · politica_despacho_extraordinario.md § Cuándo aplica
> ¿Despachan los sábados?
  TF-IDF     0.277 · politica_despacho.md § Días y horario de despacho
  Embeddings 0.562 · politica_despacho.md § Días y horario de despacho
> ¿Quién autoriza un envío urgente?
  TF-IDF     0.242 · politica_despacho_extraordinario.md § Costo
  Embeddings 0.540 · politica_despacho_extraordinario.md § Aprobación
> ¿Cuántas entregas tardías tuvo C-1002?
  TF-IDF     0.000 · politica_despacho.md § Días y horario de despacho
  Embeddings 0.379 · politica_despacho.md § Capacidad diaria
```

**Resultado:** embeddings corrige el caso de sinónimos (#4) pero también falla la #2 (la sección "Cuándo aplica" repite "despacho extraordinario"). Con embeddings ningún puntaje es 0: la #5 obtiene 0.379, así que hace falta un umbral (~0.45) entre las correctas (≥ 0.540) y la irrelevante. Con ese umbral: embeddings 4/5, TF-IDF 3/5.
