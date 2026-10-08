# Contrato: señales, coeficientes y punto fijo

**Estado:** Abierto
**Prepara:** @andres332271
**Revisan:** @moreyrajulian y @EnzoFernandezz11
**Issues:** E02, A01, A04, A05
**Fuente:** [consigna vigente](../consigna-actualizada.md), [E01](frecuencia.md) y decisiones D02–D04 del [contrato técnico](../contrato-tecnico.md).

## Alcance común a ambas ramas

Ambos filtros procesan señal compleja con los mismos ocho coeficientes RRCOS y roll-off 0,5. Los símbolos QPSK tienen componentes I/Q = ±1. Enzo confirmó el upsampling 2× el 7/10/2026 mediante un upsampler separado del generador QPSK reutilizable, común a ambas cadenas. La tabla exacta de coeficientes, su orden, fase y normalización serán únicos para ambas ramas; E02/A01 los definen junto con el mapeo de bits. A04 fija formatos y tolerancias de punto fijo.

## Decisiones para trabajar en paralelo

| Punto | Valor acordado | Fuente/ejemplo | Estado |
|---|---|---|---|
| Mapeo bits → símbolos QPSK y amplitud I/Q | Dos bits por símbolo, `(b_I, b_Q)`; bit 0 → +1, bit 1 → −1. En RTL, como palabra `b[1:0]`: `b[1]` = b_I (primer bit) y `b[0]` = b_Q. I/Q = ±1 sin normalizar por √2. | Consigna vigente (±1); `qpsk()` en [`model/qpsk_rrc.py`](../../model/qpsk_rrc.py) | Propuesto (E02) |
| Upsampler 2× | `x[2m] = a[m]`, `x[2m+1] = 0`, incluido el cero tras el último símbolo; generador separado para ambas cadenas. | Confirmación de Enzo del 7/10/2026; [registro](../contrato-tecnico.md); `upsample()` en `model/qpsk_rrc.py` | Confirmado por Enzo; revisión conjunta pendiente |
| Fórmula y fase de muestreo RRCOS | Pulso RRCOS en forma cerrada (abajo), muestreado en `t_k = (k − 3,5)/2` Ts, k = 0…7: grilla simétrica ±0,25…±1,75 Ts sin tap central. | `rrc()` y `sample_times()` | Propuesto (E02) |
| Tabla `h[0]…h[7]` y orden de taps | Tabla de abajo; `h[0]` multiplica a `x[n]` en `y[n] = Σ h[k]·x[n−k]`. Simétrica, fase lineal, retardo de grupo 3,5 muestras. | `rrc_taps()`; copia en `config/project.json` | Propuesto (E02) |
| Escala de coeficientes y ganancia total | Energía unitaria, Σh² = 1. Ganancia DC Σh = 1,4007; pico por rama ante ±1: Σ\|h\| = 1,8445. | `rrc_taps()` | Propuesto (E02) |
| Formato de entrada, producto, acumulador y salida | Entrada I/Q: 2 bits con signo, complemento a 2 (valores −1, 0, +1). Resto: A04. | Tabla de formatos | Entrada propuesta (E02); resto abierto |
| Redondeo y saturación en cada corte | Por definir | — | Abierto |

## Coeficientes propuestos (E02)

Pulso, con `t` en períodos de símbolo y α = 0,5:

```
p(0)          = 1 − α + 4α/π
p(±1/(4α))    = α/√2 · [(1 + 2/π)·sin(π/(4α)) + (1 − 2/π)·cos(π/(4α))]
p(t)          = [sin(πt(1−α)) + 4αt·cos(πt(1+α))] / [πt(1 − (4αt)²)]
h[k]          = p(t_k) / √(Σ p(t_j)²),   t_k = (k − 3,5)/2
```

| k | t_k / Ts | h[k] |
|---:|---:|---:|
| 0 | −1,75 | +0,010942691568693055 |
| 1 | −1,25 | −0,11095557645481882 |
| 2 | −0,75 | +0,11095557645481889 |
| 3 | −0,25 | +0,6893895688276623 |
| 4 | +0,25 | +0,6893895688276623 |
| 5 | +0,75 | +0,11095557645481889 |
| 6 | +1,25 | −0,11095557645481882 |
| 7 | +1,75 | +0,010942691568693055 |

Regenerar con `python3 model/qpsk_rrc.py`; `tests/test_qpsk_rrc.py` comprueba que coincida con `config/project.json`. Con 8 taps a 2× el pulso abarca solo 4 símbolos, así que la atenuación fuera de banda es pobre; es una limitación de la consigna, no del redondeo. La salida real cumple |y| ≤ Σ|h| ≈ 1,845 por rama, de modo que necesita al menos 2 bits enteros con signo; A04 fija los fraccionarios.

Ejemplo (semilla 1, 4 símbolos):

| m | b_I b_Q | a[m] | x[2m] | x[2m+1] |
|---:|---|---|---|---|
| 0 | 0 1 | +1 − j | +1 − j | 0 |
| 1 | 1 1 | −1 − j | −1 − j | 0 |
| 2 | 0 0 | +1 + j | +1 + j | 0 |
| 3 | 1 1 | −1 − j | −1 − j | 0 |

## Tabla de formatos a completar tras el barrido SQNR

| Nodo | Con signo | Bits totales | Bits fraccionarios | Rango | Política al reducir bits |
|---|---|---:|---:|---|---|
| Entrada I/Q | Sí | 2 | 0 | {−1, 0, +1} | No se reduce (exacta) |
| Coeficientes | — | — | — | — | — |
| Producto | — | — | — | — | — |
| Acumulador | — | — | — | — | — |
| Salida I/Q | — | — | — | — | — |

## Ejemplos obligatorios antes de aprobar

1. Una secuencia QPSK breve con los símbolos complejos y las muestras 2× exactas.
2. Tabla de los ocho coeficientes con precisión suficiente para reproducirla, la fórmula o script que la genera y la respuesta al impulso con índice de muestra.
3. Un ejemplo de multiplicación/acumulación en punto fijo que muestre signo, redondeo y saturación.
4. Archivo de configuración/semilla que regenere los vectores, y evidencia SQNR ≥ 40 dB con la definición acordada.

Al aprobar, copiar **solo los valores consumidos por código** a `config/project.json`. El modelo, RTL y testbench deben leer o derivar el mismo orden y escala.
