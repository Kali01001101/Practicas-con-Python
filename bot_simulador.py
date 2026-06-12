#!/usr/bin/env python3
"""
BOT SIMULADOR DE ORDENES
========================
Ejecuta tus directrices de trading sobre datos de precio reales
(velas exportadas de TradingView u otra plataforma) SIN dinero real,
y registra los trades cerrados en operaciones.csv para que el
analizador los compare por estrategia.

Uso:
    python3 bot_simulador.py directrices.txt velas_ejemplo.csv
    python3 bot_simulador.py mis_ordenes.txt EURUSD_M15.csv --csv operaciones.csv
    python3 bot_simulador.py directrices.txt velas.csv --solo-informe   (no escribe el CSV)

Como conseguir las velas desde TradingView:
    abrir el grafico -> menu del grafico -> "Exportar datos del grafico" -> CSV.
    El bot acepta columnas: fecha/time/date, open, high/max, low/min, close.

Logica de ejecucion (conservadora):
  - La orden queda PENDIENTE hasta que una vela toca el precio de entrada.
  - Una vez abierta, se revisa vela a vela si toca SL o TP.
  - Si una misma vela toca SL y TP a la vez, se asume SL (peor caso) y se avisa.
"""

import csv
import os
import re
import sys

# ----------------------------------------------------------------------
# Lectura de directrices
# ----------------------------------------------------------------------
CLAVES_OBLIGATORIAS = ("estrategia", "activo", "direccion", "entrada",
                       "sl", "tp", "riesgo_usd")

RE_NIVEL = re.compile(
    r"(?P<pct>\d+(?:\.\d+)?)\s*%\s*entre\s*(?P<a>\d+(?:\.\d+)?)\s*y\s*(?P<b>\d+(?:\.\d+)?)",
    re.IGNORECASE,
)


def parsear_entrada(texto):
    """Acepta un precio fijo ('1.0750') o un nivel relativo
    ('50% entre 1.0700 y 1.0800'). El % se mide desde el menor hacia el mayor."""
    texto = texto.strip()
    m = RE_NIVEL.match(texto)
    if m:
        pct = float(m.group("pct")) / 100
        a, b = float(m.group("a")), float(m.group("b"))
        return round(min(a, b) + pct * abs(a - b), 6)
    return float(texto)


def leer_directrices(ruta):
    with open(ruta, encoding="utf-8") as f:
        lineas = f.readlines()

    ordenes, bloque = [], {}
    for linea in lineas + [""]:        # linea vacia final para cerrar el ultimo bloque
        linea = linea.strip()
        if linea.startswith("#"):
            continue
        if not linea:
            if bloque:
                ordenes.append(bloque)
                bloque = {}
            continue
        if ":" not in linea:
            raise ValueError(f"Linea invalida en directrices: '{linea}' (formato: clave: valor)")
        clave, valor = linea.split(":", 1)
        bloque[clave.strip().lower()] = valor.strip()

    validas = []
    for i, o in enumerate(ordenes, 1):
        faltan = [c for c in CLAVES_OBLIGATORIAS if c not in o]
        if faltan:
            print(f"  ! Directriz #{i} ignorada: faltan campos {faltan}")
            continue
        direccion = o["direccion"].lower()
        if direccion not in ("compra", "venta"):
            print(f"  ! Directriz #{i} ignorada: direccion debe ser 'compra' o 'venta'")
            continue
        try:
            orden = {
                "estrategia": o["estrategia"],
                "activo": o["activo"],
                "direccion": "long" if direccion == "compra" else "short",
                "entrada": parsear_entrada(o["entrada"]),
                "sl": float(o["sl"]),
                "tp": float(o["tp"]),
                "riesgo_usd": float(o["riesgo_usd"]),
                "notas": o.get("notas", ""),
            }
        except ValueError as e:
            print(f"  ! Directriz #{i} ignorada: {e}")
            continue

        # Sanidad: el SL tiene que estar del lado correcto de la entrada
        if orden["direccion"] == "long" and not (orden["sl"] < orden["entrada"] < orden["tp"]):
            print(f"  ! Directriz #{i} ignorada: en una compra debe ser SL < entrada < TP")
            continue
        if orden["direccion"] == "short" and not (orden["tp"] < orden["entrada"] < orden["sl"]):
            print(f"  ! Directriz #{i} ignorada: en una venta debe ser TP < entrada < SL")
            continue
        validas.append(orden)
    return validas


# ----------------------------------------------------------------------
# Lectura de velas
# ----------------------------------------------------------------------
ALIAS = {
    "fecha": ("fecha", "time", "date", "datetime", "tiempo"),
    "open": ("open", "apertura", "abre"),
    "high": ("high", "max", "maximo", "máximo"),
    "low": ("low", "min", "minimo", "mínimo"),
    "close": ("close", "cierre", "cierra"),
}


def leer_velas(ruta):
    with open(ruta, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    if not filas:
        raise ValueError(f"El archivo de velas '{ruta}' esta vacio.")

    columnas = {c.strip().lower(): c for c in filas[0].keys()}
    mapa = {}
    for destino, nombres in ALIAS.items():
        for n in nombres:
            if n in columnas:
                mapa[destino] = columnas[n]
                break
        else:
            raise ValueError(f"No encuentro la columna '{destino}' en {ruta} "
                             f"(columnas detectadas: {list(columnas)})")

    velas = []
    for fila in filas:
        velas.append({
            "fecha": fila[mapa["fecha"]],
            "open": float(fila[mapa["open"]]),
            "high": float(fila[mapa["high"]]),
            "low": float(fila[mapa["low"]]),
            "close": float(fila[mapa["close"]]),
        })
    return velas


# ----------------------------------------------------------------------
# Motor de simulacion
# ----------------------------------------------------------------------
def simular(orden, velas):
    """Recorre las velas y devuelve la orden con su resultado."""
    estado = "pendiente"
    for vela in velas:
        if estado == "pendiente":
            if vela["low"] <= orden["entrada"] <= vela["high"]:
                estado = "abierta"
                orden["fecha_apertura"] = vela["fecha"]
            else:
                continue

        # Orden abierta: revisar SL y TP en esta vela
        if orden["direccion"] == "long":
            toca_sl = vela["low"] <= orden["sl"]
            toca_tp = vela["high"] >= orden["tp"]
        else:
            toca_sl = vela["high"] >= orden["sl"]
            toca_tp = vela["low"] <= orden["tp"]

        if toca_sl and toca_tp:
            orden["ambiguo"] = True       # peor caso: contamos el SL
            toca_tp = False
        if toca_sl:
            cerrar(orden, "SL", orden["sl"], vela["fecha"])
            return orden
        if toca_tp:
            cerrar(orden, "TP", orden["tp"], vela["fecha"])
            return orden

    orden["estado"] = estado              # quedo pendiente o abierta sin cerrar
    if estado == "abierta":
        orden["precio_actual"] = velas[-1]["close"]
    return orden


def cerrar(orden, motivo, precio_salida, fecha):
    orden["estado"] = "cerrada"
    orden["motivo_salida"] = motivo
    orden["precio_salida"] = precio_salida
    orden["fecha_cierre"] = fecha
    riesgo = abs(orden["entrada"] - orden["sl"])
    signo = 1 if orden["direccion"] == "long" else -1
    r = signo * (precio_salida - orden["entrada"]) / riesgo
    orden["resultado_r"] = r
    orden["resultado_usd"] = round(r * orden["riesgo_usd"], 2)


# ----------------------------------------------------------------------
# Registro en el diario
# ----------------------------------------------------------------------
COLUMNAS_DIARIO = ["id", "fecha_apertura", "fecha_cierre", "estrategia", "activo",
                   "direccion", "timeframe", "precio_entrada", "stop_loss",
                   "take_profit", "precio_salida", "riesgo_usd", "resultado_usd",
                   "motivo_salida", "notas"]


def registrar_en_diario(ordenes_cerradas, ruta_csv):
    existentes, ultimo_id = [], 0
    if os.path.exists(ruta_csv):
        with open(ruta_csv, newline="", encoding="utf-8") as f:
            existentes = list(csv.DictReader(f))
        ids = [int(fila["id"]) for fila in existentes if fila.get("id", "").isdigit()]
        ultimo_id = max(ids) if ids else 0

    nuevas = []
    for orden in ordenes_cerradas:
        ultimo_id += 1
        nota = "[BOT] " + orden["notas"]
        if orden.get("ambiguo"):
            nota += " | vela toco SL y TP: se asumio SL (peor caso)"
        nuevas.append({
            "id": ultimo_id,
            "fecha_apertura": orden["fecha_apertura"],
            "fecha_cierre": orden["fecha_cierre"],
            "estrategia": orden["estrategia"],
            "activo": orden["activo"],
            "direccion": orden["direccion"],
            "timeframe": "",
            "precio_entrada": orden["entrada"],
            "stop_loss": orden["sl"],
            "take_profit": orden["tp"],
            "precio_salida": orden["precio_salida"],
            "riesgo_usd": orden["riesgo_usd"],
            "resultado_usd": orden["resultado_usd"],
            "motivo_salida": orden["motivo_salida"],
            "notas": nota,
        })

    nuevo_archivo = not existentes and not os.path.exists(ruta_csv)
    with open(ruta_csv, "a", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS_DIARIO)
        if nuevo_archivo:
            escritor.writeheader()
        escritor.writerows(nuevas)
    return len(nuevas)


# ----------------------------------------------------------------------
# Informe
# ----------------------------------------------------------------------
def imprimir_resultado(ordenes):
    print("=" * 70)
    print("RESULTADO DE LA SIMULACION".center(70))
    print("=" * 70)
    for i, o in enumerate(ordenes, 1):
        cabecera = (f"\n#{i} {o['estrategia']} | {o['activo']} | "
                    f"{'COMPRA' if o['direccion'] == 'long' else 'VENTA'} "
                    f"@ {o['entrada']:.5f} (SL {o['sl']:.5f} / TP {o['tp']:.5f})")
        print(cabecera)
        if o["estado"] == "cerrada":
            print(f"   -> CERRADA en {o['motivo_salida']} @ {o['precio_salida']:.5f} "
                  f"el {o['fecha_cierre']}: {o['resultado_usd']:+.2f} USD "
                  f"({o['resultado_r']:+.2f} R)")
            if o.get("ambiguo"):
                print("   ! Una vela toco SL y TP a la vez: se conto como SL (peor caso). "
                      "Para resolverlo usa velas de menor temporalidad.")
        elif o["estado"] == "abierta":
            print(f"   -> SIGUE ABIERTA (abierta el {o['fecha_apertura']}, "
                  f"ultimo precio {o['precio_actual']:.5f}). "
                  "Volve a correr el bot con velas mas recientes.")
        else:
            print("   -> PENDIENTE: el precio nunca toco la entrada en estas velas.")
    print()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)

    ruta_directrices, ruta_velas = args[0], args[1]
    ruta_diario = "operaciones.csv"
    if "--csv" in flags:
        pass  # forma --csv ruta: la ruta viene como tercer argumento posicional
    if len(args) >= 3:
        ruta_diario = args[2]
    solo_informe = "--solo-informe" in flags

    ordenes = leer_directrices(ruta_directrices)
    if not ordenes:
        print("No hay directrices validas para ejecutar.")
        sys.exit(1)
    velas = leer_velas(ruta_velas)
    print(f"{len(ordenes)} directriz/ces validas | {len(velas)} velas "
          f"({velas[0]['fecha']} -> {velas[-1]['fecha']})\n")

    resultados = [simular(o, velas) for o in ordenes]
    imprimir_resultado(resultados)

    cerradas = [o for o in resultados if o["estado"] == "cerrada"]
    if cerradas and not solo_informe:
        n = registrar_en_diario(cerradas, ruta_diario)
        print(f"{n} trade(s) registrados en '{ruta_diario}'. "
              "Corre 'python3 analizador.py' para ver el impacto en tus estrategias.")
    elif cerradas:
        print("(--solo-informe: no se escribio nada en el diario)")


if __name__ == "__main__":
    main()
