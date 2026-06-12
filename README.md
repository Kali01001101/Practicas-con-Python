# 📊 Prueba TC — Analizador de Estrategias de Trading

Sistema simple para identificar **cuál de tus estrategias es más rentable**,
usando un diario de operaciones (CSV) y un analizador en Python.
Pensado para cuentas simuladas (demo), sin dinero real.

---

## 🚀 Cómo usarlo (3 pasos)

- **1. Registrá cada trade** en `operaciones.csv` (una fila por operación).
- **2. Corré el analizador:** `python3 analizador.py`
- **3. Leé el informe:** ranking de estrategias, métricas y señalamientos automáticos.

No hay que instalar nada: solo Python 3.

---

## 📝 Cómo registrar una operación

Columnas de `operaciones.csv`:

| Columna | Qué va | Ejemplo |
|---|---|---|
| `id` | Número correlativo | `13` |
| `fecha_apertura` / `fecha_cierre` | Formato AAAA-MM-DD | `2026-06-12` |
| `estrategia` | **El nombre que le pusiste a tu estrategia** (siempre igual, respetando mayúsculas) | `Ruptura Londres` |
| `activo` | Instrumento operado | `EURUSD` |
| `direccion` | `long` o `short` | `long` |
| `timeframe` | Temporalidad de la entrada | `M15` |
| `precio_entrada` | Precio de entrada | `1.0750` |
| `stop_loss` | Precio del SL (⚠️ siempre poner uno) | `1.0730` |
| `take_profit` | Precio del TP | `1.0790` |
| `precio_salida` | Precio real de cierre | `1.0790` |
| `riesgo_usd` | Cuánto arriesgabas si saltaba el SL | `100` |
| `resultado_usd` | Resultado final (negativo si perdiste) | `200` |
| `motivo_salida` | `TP`, `SL` o `manual` | `TP` |
| `notas` | Contexto, errores, qué viste | `Falsa ruptura` |

> 💡 **Regla de oro:** registrá el trade apenas lo cerrás, incluido el motivo
> de salida. El dato más valioso del diario es saber si respetaste tu plan.

---

## 📈 Qué mide el informe (y por qué importa)

- **🏆 Ranking por expectancia:** cuánto ganás *en promedio por cada trade* de esa estrategia. Es EL número para comparar estrategias entre sí.
- **Profit factor:** ganancia bruta ÷ pérdida bruta. `> 1.5` sólido, `< 1` pierde dinero.
- **Win rate:** % de trades ganadores. Solo, no dice nada: un 40% de acierto con buen R/R puede ser muy rentable.
- **Expectancia en R:** resultado medido en unidades de riesgo (1R = lo que arriesgaste). Permite comparar estrategias aunque cambies el tamaño de posición.
- **R/R planeado:** distancia al TP ÷ distancia al SL. Si es `< 1`, arriesgás más de lo que buscás ganar.
- **Salidas TP / SL / manual:** mide tu **disciplina**. Muchas salidas manuales = estás cortando ganadores o aguantando perdedores.
- **Racha de pérdidas y drawdown:** cuánto dolor seguido tuviste que bancar. Clave para dimensionar el riesgo por trade.

---

## 🚨 Señalamientos automáticos

El analizador te avisa solo cuando detecta:

- 🔴 Profit factor menor a 1 (la estrategia pierde plata tal como está).
- 🟡 Muestra menor a 30 trades (los números todavía pueden ser suerte).
- 🟡 R/R planeado promedio menor a 1.
- 🔴 Operaciones registradas **sin stop loss**.
- 🟡 Más del 30% de cierres manuales (posible falta de disciplina).
- 🟡 Rachas de 4+ pérdidas seguidas.

---

## 🏷️ Etiquetas del informe

- `[RENTABLE]` → profit factor ≥ 1.5 y expectancia positiva.
- `[AL LIMITE]` → gana, pero con poco margen; cualquier cambio la vuelve perdedora.
- `[PIERDE DINERO]` → profit factor < 1.
- `[MUESTRA CHICA]` → menos de 30 trades: no saques conclusiones todavía.

---

## 🤖 Bot simulador de órdenes

Le "enseñás" a operar escribiendo directrices en `directrices.txt` y el bot
las ejecuta sobre datos de precio reales, **sin dinero real**, registrando los
resultados en el diario.

- **1. Escribí tus directrices** en `directrices.txt`. Ejemplo (equivale a
  *"en el 50% entre el máximo y el mínimo abrí una compra, SL y TP en X"*):

  ```
  estrategia: Ruptura Londres
  activo: EURUSD
  direccion: compra
  entrada: 50% entre 1.0700 y 1.0800
  sl: 1.0720
  tp: 1.0810
  riesgo_usd: 100
  ```

- **2. Exportá las velas desde TradingView:** abrí el gráfico → menú → *Exportar datos del gráfico* → CSV.
- **3. Corré el bot:** `python3 bot_simulador.py directrices.txt velas.csv`
- **4. El bot te informa** qué orden se activó, cuál cerró en TP/SL y cuál quedó pendiente, y **registra solo** los trades cerrados en `operaciones.csv` (marcados con `[BOT]`).
- Para probar sin escribir en el diario: agregá `--solo-informe`.
- Probalo ya mismo con los datos incluidos: `python3 bot_simulador.py directrices.txt velas_ejemplo.csv --solo-informe`

> ⚠️ **Criterio conservador:** si una misma vela toca SL y TP, el bot cuenta
> la pérdida (peor caso) y te lo señala. Usá velas de menor temporalidad para
> resolver la ambigüedad.

---

## ⚡ Bot MT5 (ejecución en vivo)

Coloca tus directrices como **órdenes pendientes reales en MetaTrader 5**,
con SL/TP y lote calculado automáticamente según tu riesgo en USD.

- **Requisitos (solo Windows):**
  - MT5 instalado, **abierto y logueado** en tu cuenta.
  - `pip install MetaTrader5`
  - En MT5: *Herramientas → Opciones → Expert Advisors → permitir trading algorítmico*.
- **Comandos:**
  - `python bot_mt5.py colocar directrices.txt` → coloca las órdenes pendientes (elige solo BUY/SELL LIMIT o STOP según dónde esté el precio).
  - `python bot_mt5.py estado` → muestra las órdenes y posiciones del bot.
  - `python bot_mt5.py sincronizar` → baja los trades cerrados al diario `operaciones.csv` (etiquetados `[MT5]`, sin duplicar), listos para el analizador.
- **Cómo funciona por dentro:**
  - Usa el mismo formato de `directrices.txt` que el simulador (incluido el `50% entre X y X`).
  - Calcula el **lote** para que, si salta el SL, pierdas ≈ tu `riesgo_usd` (te informa el riesgo real tras el redondeo del broker).
  - Marca sus órdenes con un número mágico: **no toca tus operaciones manuales**.
  - El nombre de la estrategia viaja en el comentario de la orden, así el cierre vuelve al diario con la estrategia correcta.
  - Al conectar te informa si la cuenta es DEMO o REAL.

---

## ⚙️ Ajustes

Los umbrales (muestra mínima, profit factor, R/R) están al inicio de
`analizador.py`, en la sección *Configuración*, y se pueden cambiar.

El archivo `operaciones.csv` viene con **12 trades de ejemplo** para que veas
el informe funcionando. Borralos cuando empieces a cargar los tuyos
(dejá la primera fila, que es el encabezado).
