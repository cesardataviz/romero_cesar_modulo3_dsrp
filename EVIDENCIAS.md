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
