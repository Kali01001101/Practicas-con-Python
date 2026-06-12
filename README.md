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

## ⚙️ Ajustes

Los umbrales (muestra mínima, profit factor, R/R) están al inicio de
`analizador.py`, en la sección *Configuración*, y se pueden cambiar.

El archivo `operaciones.csv` viene con **12 trades de ejemplo** para que veas
el informe funcionando. Borralos cuando empieces a cargar los tuyos
(dejá la primera fila, que es el encabezado).
