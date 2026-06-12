#!/usr/bin/env python3
"""
ANALIZADOR DE ESTRATEGIAS DE TRADING
=====================================
Lee el diario de operaciones (operaciones.csv) y genera un informe
comparativo por estrategia, con etiquetas y señalamientos automaticos.

Uso:
    python3 analizador.py                  # usa operaciones.csv
    python3 analizador.py mi_archivo.csv   # usa otro archivo

No requiere instalar nada: solo Python 3 estandar.
"""

import csv
import sys
from collections import defaultdict

# ----------------------------------------------------------------------
# Configuracion (ajustar a gusto)
# ----------------------------------------------------------------------
MUESTRA_MINIMA = 30      # trades minimos para considerar fiable una estadistica
PF_BUENO = 1.5           # profit factor a partir del cual se considera solido
PF_MALO = 1.0            # por debajo de esto la estrategia pierde dinero
RR_MINIMO = 1.0          # ratio riesgo/beneficio planeado minimo aceptable


def leer_operaciones(ruta):
    operaciones = []
    with open(ruta, newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            operaciones.append(fila)
    return operaciones


def num(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def calcular_r(op):
    """Devuelve (r_planeado, r_obtenido) de una operacion, o (None, None).

    R = cuanto se gano/perdio medido en unidades de riesgo.
    r_planeado usa el TP; r_obtenido usa el precio de salida real.
    """
    entrada = num(op.get("precio_entrada"))
    sl = num(op.get("stop_loss"))
    tp = num(op.get("take_profit"))
    salida = num(op.get("precio_salida"))
    if entrada is None or sl is None:
        return None, None

    riesgo = abs(entrada - sl)
    if riesgo == 0:
        return None, None

    signo = 1 if op.get("direccion", "").strip().lower() == "long" else -1
    r_plan = signo * (tp - entrada) / riesgo if tp is not None else None
    r_real = signo * (salida - entrada) / riesgo if salida is not None else None
    return r_plan, r_real


def analizar_estrategia(nombre, trades):
    resultados = [num(t.get("resultado_usd")) for t in trades]
    resultados = [r for r in resultados if r is not None]

    ganadores = [r for r in resultados if r > 0]
    perdedores = [r for r in resultados if r < 0]

    bruto_ganado = sum(ganadores)
    bruto_perdido = abs(sum(perdedores))

    stats = {
        "nombre": nombre,
        "n": len(trades),
        "neto_usd": sum(resultados),
        "win_rate": len(ganadores) / len(resultados) * 100 if resultados else 0,
        "profit_factor": bruto_ganado / bruto_perdido if bruto_perdido else float("inf"),
        "ganancia_media": sum(ganadores) / len(ganadores) if ganadores else 0,
        "perdida_media": sum(perdedores) / len(perdedores) if perdedores else 0,
    }

    # Expectancia: cuanto se espera ganar (en USD) por cada trade tomado
    stats["expectancia_usd"] = stats["neto_usd"] / len(resultados) if resultados else 0

    # R planeado y obtenido
    rs_plan, rs_real = [], []
    sin_sl = 0
    for t in trades:
        r_plan, r_real = calcular_r(t)
        if r_plan is not None:
            rs_plan.append(r_plan)
        if r_real is not None:
            rs_real.append(r_real)
        if num(t.get("stop_loss")) is None:
            sin_sl += 1
    stats["rr_plan_medio"] = sum(rs_plan) / len(rs_plan) if rs_plan else None
    stats["expectancia_r"] = sum(rs_real) / len(rs_real) if rs_real else None
    stats["sin_sl"] = sin_sl

    # Como se cierran los trades (disciplina de ejecucion)
    salidas = defaultdict(int)
    for t in trades:
        salidas[t.get("motivo_salida", "desconocido").strip().lower()] += 1
    stats["salidas"] = dict(salidas)

    # Racha maxima de perdidas y drawdown de la curva de capital
    racha = racha_max = 0
    equity = pico = dd_max = 0.0
    for r in resultados:
        racha = racha + 1 if r < 0 else 0
        racha_max = max(racha_max, racha)
        equity += r
        pico = max(pico, equity)
        dd_max = max(dd_max, pico - equity)
    stats["racha_perdidas"] = racha_max
    stats["drawdown_usd"] = dd_max

    return stats


def etiqueta(stats):
    """Etiqueta global de la estrategia segun sus numeros."""
    if stats["n"] < MUESTRA_MINIMA:
        base = "MUESTRA CHICA"
    else:
        base = "MUESTRA OK"
    pf = stats["profit_factor"]
    if pf >= PF_BUENO and stats["expectancia_usd"] > 0:
        return f"[RENTABLE | {base}]"
    if pf >= PF_MALO:
        return f"[AL LIMITE | {base}]"
    return f"[PIERDE DINERO | {base}]"


def senalamientos(stats):
    """Avisos proactivos: cosas que conviene mirar de cada estrategia."""
    avisos = []
    if stats["n"] < MUESTRA_MINIMA:
        avisos.append(
            f"Solo {stats['n']} trades registrados: con menos de {MUESTRA_MINIMA} "
            "operaciones los numeros pueden ser pura suerte. Segui registrando antes de sacar conclusiones."
        )
    if stats["profit_factor"] < PF_MALO:
        avisos.append(
            "Profit factor menor a 1: tal como esta, esta estrategia PIERDE dinero. "
            "Revisa si el problema es la tasa de acierto o el tamano de las perdidas."
        )
    if stats["rr_plan_medio"] is not None and stats["rr_plan_medio"] < RR_MINIMO:
        avisos.append(
            f"El ratio riesgo/beneficio planeado promedio es {stats['rr_plan_medio']:.2f} "
            f"(menor a {RR_MINIMO}): arriesgas mas de lo que buscas ganar. "
            "Necesitarias una tasa de acierto muy alta para que cierre."
        )
    if stats["sin_sl"] > 0:
        avisos.append(
            f"{stats['sin_sl']} operacion(es) sin stop loss registrado: "
            "operar sin SL es el riesgo numero uno de fundir la cuenta."
        )
    total_salidas = sum(stats["salidas"].values())
    manuales = stats["salidas"].get("manual", 0)
    if total_salidas and manuales / total_salidas > 0.3:
        avisos.append(
            f"{manuales} de {total_salidas} trades cerrados a mano: "
            "si cortas los ganadores antes del TP, estas matando la expectancia. "
            "Compara el R obtenido contra el R planeado."
        )
    if stats["racha_perdidas"] >= 4:
        avisos.append(
            f"Racha maxima de {stats['racha_perdidas']} perdidas seguidas: "
            "asegurate de que el riesgo por trade aguante una racha asi sin dano psicologico ni de capital."
        )
    return avisos


def fmt(valor, decimales=2, sufijo=""):
    if valor is None:
        return "s/d"
    if valor == float("inf"):
        return "inf"
    return f"{valor:.{decimales}f}{sufijo}"


def imprimir_informe(operaciones):
    por_estrategia = defaultdict(list)
    for op in operaciones:
        por_estrategia[op.get("estrategia", "Sin nombre").strip()].append(op)

    todas = [analizar_estrategia(n, t) for n, t in sorted(por_estrategia.items())]
    # Ranking: primero la de mayor expectancia por trade
    todas.sort(key=lambda s: s["expectancia_usd"], reverse=True)

    print("=" * 70)
    print("INFORME DE ESTRATEGIAS".center(70))
    print(f"({len(operaciones)} operaciones | {len(todas)} estrategias)".center(70))
    print("=" * 70)

    for puesto, s in enumerate(todas, 1):
        print(f"\n#{puesto}  {s['nombre'].upper()}  {etiqueta(s)}")
        print("-" * 70)
        print(f"  Trades:             {s['n']}")
        print(f"  Resultado neto:     {fmt(s['neto_usd'], 2, ' USD')}")
        print(f"  Win rate:           {fmt(s['win_rate'], 1, '%')}")
        print(f"  Profit factor:      {fmt(s['profit_factor'])}")
        print(f"  Expectancia/trade:  {fmt(s['expectancia_usd'], 2, ' USD')}"
              f"  ({fmt(s['expectancia_r'], 2, ' R')})")
        print(f"  Ganancia media:     {fmt(s['ganancia_media'], 2, ' USD')}"
              f"  | Perdida media: {fmt(s['perdida_media'], 2, ' USD')}")
        print(f"  R/R planeado medio: {fmt(s['rr_plan_medio'])}")
        print(f"  Racha de perdidas:  {s['racha_perdidas']}"
              f"  | Drawdown max: {fmt(s['drawdown_usd'], 2, ' USD')}")
        salidas = ", ".join(f"{k}: {v}" for k, v in sorted(s["salidas"].items()))
        print(f"  Salidas:            {salidas}")

        avisos = senalamientos(s)
        if avisos:
            print("\n  SEÑALAMIENTOS:")
            for a in avisos:
                print(f"   ! {a}")

    print("\n" + "=" * 70)
    if todas:
        mejor = todas[0]
        print(f"CONCLUSION: la estrategia con mejor expectancia por trade es "
              f"'{mejor['nombre']}' ({fmt(mejor['expectancia_usd'], 2, ' USD/trade')}).")
        if mejor["n"] < MUESTRA_MINIMA:
            print(f"OJO: todavia con muestra chica ({mejor['n']} trades). "
                  "El ranking puede cambiar con mas datos.")
    print("=" * 70)


def main():
    ruta = sys.argv[1] if len(sys.argv) > 1 else "operaciones.csv"
    try:
        operaciones = leer_operaciones(ruta)
    except FileNotFoundError:
        print(f"No se encontro el archivo '{ruta}'. "
              "Registra tus trades ahi primero (mira el README).")
        sys.exit(1)
    if not operaciones:
        print(f"El archivo '{ruta}' esta vacio: registra al menos una operacion.")
        sys.exit(1)
    imprimir_informe(operaciones)


if __name__ == "__main__":
    main()
