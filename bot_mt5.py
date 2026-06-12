#!/usr/bin/env python3
"""
BOT MT5 — EJECUCION EN VIVO DE TUS DIRECTRICES
==============================================
Coloca tus directrices como ordenes pendientes reales en MetaTrader 5
(con SL y TP), calcula el lote segun tu riesgo en USD, y baja los trades
cerrados al diario (operaciones.csv) para analizarlos por estrategia.

Requisitos:
  - Windows con MetaTrader 5 instalado, ABIERTO y logueado en tu cuenta.
  - pip install MetaTrader5
  - En MT5: Herramientas -> Opciones -> Expert Advisors -> permitir trading algoritmico.

Uso:
  python bot_mt5.py colocar [directrices.txt]   -> coloca las ordenes pendientes
  python bot_mt5.py estado                      -> ordenes y posiciones del bot
  python bot_mt5.py sincronizar [operaciones.csv] -> registra los cierres en el diario

Las directrices usan el MISMO formato que el bot simulador (ver directrices.txt).
El bot marca todo lo suyo con un numero magico, asi no toca ordenes manuales tuyas.
"""

import csv
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta

from bot_simulador import leer_directrices, COLUMNAS_DIARIO

try:
    import MetaTrader5 as mt5
except ImportError:
    print("Falta el paquete MetaTrader5 (solo funciona en Windows):")
    print("    pip install MetaTrader5")
    sys.exit(1)

MAGIC = 51210                      # identifica las ordenes de este bot
REGISTRO_SINCRONIZADOS = ".mt5_sincronizados.txt"
DIAS_HISTORIAL = 120


# ----------------------------------------------------------------------
# Conexion
# ----------------------------------------------------------------------
def conectar():
    if not mt5.initialize():
        print(f"No pude conectar con el terminal MT5: {mt5.last_error()}")
        print("Verifica que MetaTrader 5 este abierto y logueado.")
        sys.exit(1)
    cuenta = mt5.account_info()
    if cuenta is None:
        print("Conecte con el terminal pero no hay cuenta logueada.")
        sys.exit(1)
    modo = {0: "REAL", 1: "DEMO", 2: "CONCURSO"}.get(cuenta.trade_mode, "?")
    print(f"Conectado: cuenta {cuenta.login} ({modo}) | {cuenta.server} | "
          f"balance {cuenta.balance:.2f} {cuenta.currency}")
    if modo == "REAL":
        print("  ! ATENCION: cuenta REAL. Las ordenes que coloque operan dinero real.")
    print()
    return cuenta


# ----------------------------------------------------------------------
# Colocar ordenes
# ----------------------------------------------------------------------
def calcular_lote(info, entrada, sl, riesgo_usd):
    """Lote para que, si salta el SL, la perdida sea ~riesgo_usd."""
    dist = abs(entrada - sl)
    if not info.trade_tick_size or not info.trade_tick_value:
        return None, "el simbolo no informa tick size/value"
    riesgo_por_lote = dist / info.trade_tick_size * info.trade_tick_value
    if riesgo_por_lote <= 0:
        return None, "riesgo por lote nulo (revisa entrada y SL)"
    lotes = riesgo_usd / riesgo_por_lote
    paso = info.volume_step or 0.01
    lotes = math.floor(lotes / paso) * paso
    lotes = round(max(info.volume_min, min(lotes, info.volume_max)), 8)
    riesgo_real = lotes * riesgo_por_lote
    return lotes, f"riesgo real ~{riesgo_real:.2f} USD"


def tipo_de_orden(direccion, entrada, tick):
    """Limit si el precio tiene que volver hasta la entrada; stop si tiene que ir a buscarla."""
    if direccion == "long":
        return (mt5.ORDER_TYPE_BUY_LIMIT, "BUY LIMIT") if entrada < tick.ask \
            else (mt5.ORDER_TYPE_BUY_STOP, "BUY STOP")
    return (mt5.ORDER_TYPE_SELL_LIMIT, "SELL LIMIT") if entrada > tick.bid \
        else (mt5.ORDER_TYPE_SELL_STOP, "SELL STOP")


def colocar(ruta_directrices):
    ordenes = leer_directrices(ruta_directrices)
    if not ordenes:
        print("No hay directrices validas.")
        return
    conectar()

    for i, o in enumerate(ordenes, 1):
        simbolo = o["activo"]
        print(f"#{i} {o['estrategia']} | {simbolo} | "
              f"{'COMPRA' if o['direccion'] == 'long' else 'VENTA'} @ {o['entrada']}")

        if not mt5.symbol_select(simbolo, True):
            print(f"   ! Simbolo '{simbolo}' no disponible en tu broker. Salteada.\n")
            continue
        info = mt5.symbol_info(simbolo)
        tick = mt5.symbol_info_tick(simbolo)
        if info is None or tick is None:
            print(f"   ! No pude obtener datos de '{simbolo}'. Salteada.\n")
            continue

        lotes, detalle = calcular_lote(info, o["entrada"], o["sl"], o["riesgo_usd"])
        if lotes is None:
            print(f"   ! No pude calcular el lote: {detalle}. Salteada.\n")
            continue

        tipo, nombre_tipo = tipo_de_orden(o["direccion"], o["entrada"], tick)
        solicitud = {
            "action": mt5.TRADE_ACTION_PENDING,
            "symbol": simbolo,
            "volume": lotes,
            "type": tipo,
            "price": round(o["entrada"], info.digits),
            "sl": round(o["sl"], info.digits),
            "tp": round(o["tp"], info.digits),
            "magic": MAGIC,
            "comment": o["estrategia"][:26],
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }
        res = mt5.order_send(solicitud)
        if res is None:
            print(f"   ! order_send fallo: {mt5.last_error()}\n")
        elif res.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"   -> COLOCADA: {nombre_tipo} {lotes} lotes "
                  f"(SL {o['sl']} / TP {o['tp']}, {detalle}). Ticket {res.order}\n")
        else:
            print(f"   ! RECHAZADA por el broker (codigo {res.retcode}): {res.comment}\n")

    mt5.shutdown()


# ----------------------------------------------------------------------
# Estado
# ----------------------------------------------------------------------
def estado():
    conectar()
    pendientes = [o for o in (mt5.orders_get() or ()) if o.magic == MAGIC]
    abiertas = [p for p in (mt5.positions_get() or ()) if p.magic == MAGIC]

    print(f"ORDENES PENDIENTES DEL BOT: {len(pendientes)}")
    for o in pendientes:
        print(f"  - [{o.comment}] {o.symbol} {o.volume_current} lotes @ {o.price_open} "
              f"(SL {o.sl} / TP {o.tp}) ticket {o.ticket}")
    print(f"\nPOSICIONES ABIERTAS DEL BOT: {len(abiertas)}")
    for p in abiertas:
        print(f"  - [{p.comment}] {p.symbol} {p.volume} lotes @ {p.price_open} "
              f"(SL {p.sl} / TP {p.tp}) flotante {p.profit:+.2f} USD")
    mt5.shutdown()


# ----------------------------------------------------------------------
# Sincronizar cierres con el diario
# ----------------------------------------------------------------------
def leer_ya_sincronizados():
    if not os.path.exists(REGISTRO_SINCRONIZADOS):
        return set()
    with open(REGISTRO_SINCRONIZADOS, encoding="utf-8") as f:
        return {linea.strip() for linea in f if linea.strip()}


def proximo_id(ruta_diario):
    if not os.path.exists(ruta_diario):
        return 1
    with open(ruta_diario, newline="", encoding="utf-8") as f:
        ids = [int(fila["id"]) for fila in csv.DictReader(f)
               if fila.get("id", "").isdigit()]
    return (max(ids) if ids else 0) + 1


def sincronizar(ruta_diario):
    conectar()
    desde = datetime.now() - timedelta(days=DIAS_HISTORIAL)
    hasta = datetime.now() + timedelta(days=1)
    deals = mt5.history_deals_get(desde, hasta) or ()

    por_posicion = defaultdict(list)
    for d in deals:
        if d.magic == MAGIC and d.position_id:
            por_posicion[d.position_id].append(d)

    ya = leer_ya_sincronizados()
    nuevo_id = proximo_id(ruta_diario)
    filas, sincronizadas = [], []

    for pos_id, ds in sorted(por_posicion.items()):
        if str(pos_id) in ya:
            continue
        entradas = [d for d in ds if d.entry == mt5.DEAL_ENTRY_IN]
        salidas = [d for d in ds if d.entry == mt5.DEAL_ENTRY_OUT]
        if not entradas or not salidas:
            continue                      # posicion todavia abierta
        ent, sal = entradas[0], salidas[-1]

        motivo = "manual"
        if sal.reason == mt5.DEAL_REASON_SL:
            motivo = "SL"
        elif sal.reason == mt5.DEAL_REASON_TP:
            motivo = "TP"

        # SL/TP originales: salen de la orden que abrio la posicion
        ordenes_pos = mt5.history_orders_get(position=pos_id) or ()
        sl = tp = ""
        riesgo_usd = ""
        if ordenes_pos:
            sl, tp = ordenes_pos[0].sl, ordenes_pos[0].tp
            info = mt5.symbol_info(ent.symbol)
            if sl and info and info.trade_tick_size and info.trade_tick_value:
                riesgo_usd = round(abs(ent.price - sl) / info.trade_tick_size
                                   * info.trade_tick_value * ent.volume, 2)

        resultado = round(sum(d.profit + d.commission + d.swap for d in ds), 2)
        filas.append({
            "id": nuevo_id,
            "fecha_apertura": datetime.fromtimestamp(ent.time).strftime("%Y-%m-%d %H:%M"),
            "fecha_cierre": datetime.fromtimestamp(sal.time).strftime("%Y-%m-%d %H:%M"),
            "estrategia": ent.comment or "Sin nombre",
            "activo": ent.symbol,
            "direccion": "long" if ent.type == mt5.DEAL_TYPE_BUY else "short",
            "timeframe": "",
            "precio_entrada": ent.price,
            "stop_loss": sl,
            "take_profit": tp,
            "precio_salida": sal.price,
            "riesgo_usd": riesgo_usd,
            "resultado_usd": resultado,
            "motivo_salida": motivo,
            "notas": f"[MT5] posicion {pos_id}",
        })
        sincronizadas.append(str(pos_id))
        nuevo_id += 1

    mt5.shutdown()

    if not filas:
        print("No hay cierres nuevos del bot para registrar.")
        return

    archivo_nuevo = not os.path.exists(ruta_diario)
    with open(ruta_diario, "a", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUMNAS_DIARIO)
        if archivo_nuevo:
            escritor.writeheader()
        escritor.writerows(filas)
    with open(REGISTRO_SINCRONIZADOS, "a", encoding="utf-8") as f:
        f.write("\n".join(sincronizadas) + "\n")

    print(f"{len(filas)} trade(s) nuevos registrados en '{ruta_diario}':")
    for fila in filas:
        print(f"  - [{fila['estrategia']}] {fila['activo']} {fila['direccion']} "
              f"-> {fila['motivo_salida']} {fila['resultado_usd']:+.2f} USD")
    print("\nCorre 'python analizador.py' para ver el ranking actualizado.")


def main():
    comandos = {"colocar", "estado", "sincronizar"}
    if len(sys.argv) < 2 or sys.argv[1] not in comandos:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "colocar":
        colocar(sys.argv[2] if len(sys.argv) > 2 else "directrices.txt")
    elif cmd == "estado":
        estado()
    else:
        sincronizar(sys.argv[2] if len(sys.argv) > 2 else "operaciones.csv")


if __name__ == "__main__":
    main()
