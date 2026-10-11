# evaluar_router.py
# 12 casos de evaluación del router (§8.1): solicitud y destino esperado.
from router import enrutar

CASOS = [
    ("¿Pueden entregar 12 EDGE-ORIN a C-1003 el jueves?", "CLARIFY"),
    ("¿Pueden despachar 5 PLC-S7M a C-1004 en Arequipa para el 22?", "CLARIFY"),
    ("C-1008 necesita 6 CAM-GIGE5 para el viernes 23.", "TOOLS"),
    ("¿Cuántas entregas tardías ha tenido Agroindustrial del Norte?", "SQL"),
    ("¿Cuál es la política para un despacho extraordinario?", "RAG"),
    ("¿Cuál es el plazo estándar de entrega a Piura?", "RAG"),
    ("Envíen 3 EDGE-NANO a C-1007 en Iquitos lo antes posible.", "TOOLS"),
    ("C-1099 quiere 10 SENS-PROX para la próxima semana.", "CLARIFY"),
    ("Necesito unos equipos para pronto.", "CLARIFY"),
    ("Hola, ¿qué puedes hacer por mí?", "DIRECT"),
    ("¿Qué productos le hemos vendido a C-1003 en los últimos 3 meses?", "SQL"),
    ("¿Quién autoriza un envío urgente?", "RAG"),
    # Casos nuevos (no usados al ajustar el prompt): validan que el criterio generaliza
    ("C-1005 necesita 4 LENS-12MM cuanto antes.", "TOOLS"),
    ("¿Pueden enviar 2 PLC-S7M a C-1006 a fin de mes?", "CLARIFY"),
]

if __name__ == "__main__":
    aciertos = 0
    for i, (solicitud, esperado) in enumerate(CASOS, start=1):
        print(f"\n{i:>2}. {solicitud}")
        r = enrutar(solicitud)
        acierto = r["destino"] == esperado
        aciertos += acierto
        marca = "OK " if acierto else "ERR"
        print(f"    [{marca}] esperado={esperado} · obtenido={r['destino']} "
              f"({r['origen']}, confianza={r['confianza']})")
        print(f"    datos: cliente={r['cliente_id']} sku={r['sku']} cantidad={r['cantidad']} fecha={r['fecha']}")
        print(f"    motivo: {r['motivo']}")
    print(f"\nAciertos: {aciertos}/{len(CASOS)}")