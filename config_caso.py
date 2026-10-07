import random

CASO_ID = "LOG-009"
VARIANTE = "Logística"
SEMILLA = 9911
rng = random.Random(SEMILLA)

capacidad_diaria = rng.randint(20, 60)             # unidades/día
costo_extraordinario = rng.choice([100, 300, 400]) # USD
ventana_entrega_dias = rng.choice([2, 3, 5])       # días hábiles



def mostrar_config():
    print(f"CASO_ID={CASO_ID}, SEMILLA={SEMILLA}, VARIANTE={VARIANTE}, capacidad_diaria={capacidad_diaria}, ventana_entrega_dias={ventana_entrega_dias}, costo_extraordinario={costo_extraordinario}")
    print(f"capacidad_diaria={capacidad_diaria} unidades/día")
    print(f"ventana_entrega_dias={ventana_entrega_dias} días hábiles")
    print(f"costo_extraordinario={costo_extraordinario} USD")


if __name__ == "__main__":
    mostrar_config()
