# consultas_sql.py
# Consultas SQL parametrizadas sobre el historial (datos transaccionales del pasado).
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "andessupply.db"


def consultar(sql, parametros):
    """Ejecuta una consulta parametrizada y devuelve una lista de diccionarios."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(fila) for fila in conn.execute(sql, parametros)]
    finally:
        conn.close()

def cliente_existe(cliente_id):
    """True si el cliente está registrado en la tabla clientes."""
    sql = "SELECT 1 FROM clientes WHERE cliente_id = ?"
    return len(consultar(sql, (cliente_id,))) > 0

def entregas_tardias(cliente_id):
    """Ventas de un cliente entregadas después de la fecha prometida."""
    sql = """
        SELECT venta_id, sku, cantidad, fecha_prometida, fecha_entregada,
               CAST(julianday(fecha_entregada) - julianday(fecha_prometida) AS INTEGER) AS dias_retraso
        FROM ventas
        WHERE cliente_id = ?
          AND fecha_entregada > fecha_prometida
        ORDER BY fecha_prometida
    """
    return consultar(sql, (cliente_id,))


def historial_ventas(cliente_id, desde):
    """Ventas de un cliente desde una fecha (AAAA-MM-DD), con el nombre del producto."""
    sql = """
        SELECT v.venta_id, v.fecha_prometida, v.sku, p.nombre AS producto, v.cantidad
        FROM ventas v
        JOIN productos p ON p.sku = v.sku
        WHERE v.cliente_id = ?
          AND v.fecha_prometida >= ?
        ORDER BY v.fecha_prometida
    """
    return consultar(sql, (cliente_id, desde))


def cumplimiento_entregas(cliente_id):
    """Total de entregas de un cliente y cuántas llegaron a tiempo."""
    sql = """
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN fecha_entregada <= fecha_prometida THEN 1 ELSE 0 END) AS a_tiempo
        FROM ventas
        WHERE cliente_id = ?
    """
    return consultar(sql, (cliente_id,))[0]


if __name__ == "__main__":
    print("1) Entregas tardías de C-1002:")
    for fila in entregas_tardias("C-1002"):
        print("  ", fila)
        
    print("2) Historial de C-1003 desde 2026-07-12:")
    for fila in historial_ventas("C-1003", "2026-07-12"):
        print("  ", fila)

    print("3) Cumplimiento de C-1002:", cumplimiento_entregas("C-1002"))

    print("4) Entregas tardías de C-1099 (no existe):", entregas_tardias("C-1099"))

    print("5) Entregas tardías de C-1001:", entregas_tardias("C-1001"))
    
    for cliente in ["C-1001", "C-1099"]:
        if not cliente_existe(cliente): 
            print(f"6) {cliente}: cliente no existe")
        else:
            print(f"6) {cliente}: existe, cumplimiento {cumplimiento_entregas(cliente)}")


