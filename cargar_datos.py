# Reconstruye la base SQlite desde los CSV cada vez que se ejecuta el script (mitigación de D1).

import csv
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "andessupply.db"

SCHEMA = """
CREATE TABLE clientes (
    cliente_id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    ciudad TEXT NOT NULL,
    tipo TEXT NOT NULL
);
CREATE TABLE ciudades (
    ciudad        TEXT PRIMARY KEY,
    dias_transito INTEGER NOT NULL
);
CREATE TABLE productos (
    sku        TEXT PRIMARY KEY,
    nombre     TEXT NOT NULL,
    categoria  TEXT NOT NULL,
    precio_usd REAL NOT NULL
);
CREATE TABLE inventario (
    sku              TEXT PRIMARY KEY,
    stock_disponible INTEGER NOT NULL
);
CREATE TABLE ventas (
    venta_id        TEXT PRIMARY KEY,
    cliente_id      TEXT NOT NULL,
    sku             TEXT NOT NULL,
    cantidad        INTEGER NOT NULL,
    fecha_prometida TEXT NOT NULL,
    fecha_entregada TEXT
);
CREATE TABLE despachos_programados (
    fecha                  TEXT PRIMARY KEY,
    unidades_comprometidas INTEGER NOT NULL
);
"""
TABLES = ["clientes","ciudades", "productos", "inventario", "ventas", "despachos_programados"]

def cargar_tabla(conn, tabla):
    with open(DATA_DIR / f"{tabla}.csv" , encoding = "utf-8", newline = "") as f:
        filas = list(csv.DictReader(f))
    columnas = list(filas[0].keys())
    marcadores = ", ".join("?" for _ in columnas)
    sql = f"INSERT INTO {tabla} ({', '.join(columnas)}) VALUES ({marcadores})"
    conn.executemany(sql, [tuple(fila.values()) for fila in filas])
    return len(filas)

def reconstruir_base():
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    for tabla in TABLES:
        n = cargar_tabla(conn, tabla)
        print(f"Se cargaron {n} filas en la tabla {tabla}.")
    conn.commit()
    conn.close()
    print(f"Base reconstruida en {DB_PATH.name}")

if __name__ == "__main__":
    reconstruir_base()
