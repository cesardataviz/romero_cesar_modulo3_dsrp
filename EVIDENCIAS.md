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