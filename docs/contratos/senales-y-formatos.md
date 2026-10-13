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
| Formato de entrada, producto, acumulador y salida | Entrada I/Q: 2 bits con signo, complemento a 2 (valores −1, 0, +1). Resto: [tabla de A04](#formatos-de-punto-fijo-a04). | `model/fixed_point.py` | Entrada propuesta (E02); resto propuesto (A04) |
| Redondeo y saturación en cada corte | Redondeo mitad hacia arriba, `(v + 2^(s−1)) >>> s`. Sin saturación: los anchos cubren el peor caso y el modelo falla si un valor no entra. | `model/fixed_point.py` | Propuesto (A04) |

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

## Formatos de punto fijo (A04)

`Qm.f` = m bits enteros con signo y f fraccionarios (total m+f). Todos los valores son complemento a 2. Los bits fraccionarios están en `config/project.json` (`decisions.fixed_point_format`); `widths()` de [`model/fixed_point.py`](../../model/fixed_point.py) deriva los anchos totales con cotas de peor caso.

| Nodo | Rama | Formato | Bits | Rango o cota | Corte |
|---|---|---|---:|---|---|
| Entrada I/Q | ambas | Q2.0 | 2 | {−1, 0, +1} | Exacta |
| Coeficientes `h_q` | ambas | Q1.7 | 8 | máx. 88/128 = 0,6875 | Offline, redondeo al más cercano |
| Producto `h_q·x` | tiempo | Q1.7 | 8 | ±h_q: con x ∈ {−1, 0, +1} es selección y negación, sin multiplicador | Exacto |
| Acumulador | tiempo | Q2.7 | 9 | Σ\|h_q\| = 234/128 = 1,83 | Exacto |
| Salida I/Q | ambas | Q2.7 | 9 | ≤ 1,83 + error | Tiempo: = acumulador. Frecuencia: redondeo de `work/16` |
| Banco `work` | frecuencia | Q7.5 | 12 | 42,5 (cota de todas las etapas FFT, H, IFFT) | Tras cada producto complejo |
| Twiddles W | frecuencia | Q2.8 | 10 | ±1; W₀ = 1 exige el bit entero | Offline |
| Espectro H = DFT16(`h_q`) | frecuencia | Q2.8 | 10 | máx. 1,39 | Offline, desde `h_q` |
| Producto complejo `W·B`, `X·H` | frecuencia | Q10.13 | 23 | Operandos 12 × 10 bits: cada producto real Q9.13 (22 bits) y la suma o resta de dos agrega uno | Redondeo a Q7.5 antes de escribir `work` |

**Cotas.** En la rama temporal, \|y\| ≤ Σ\|h_q\| porque cada entrada vale como máximo 1. En frecuencia, cada nodo de `work` es lineal en la ventana, `v = Σ c_n·x_n`, y \|Re v\|, \|Im v\| ≤ Σ(\|Re c_n\| + \|Im c_n\|); `work_bound()` lo evalúa en las nueve etapas con las constantes cuantizadas y suma 1 de margen por redondeo. El máximo está en la penúltima etapa de la IFFT (41,5). Un test arma la ventana QPSK de peor caso para cada nodo y comprueba que no hay overflow y que la cota no sobra un bit entero.

**Barrido** (`python3 -m model.fixed_point`, SQNR mínima en dB; filas = bits fraccionarios de coeficientes, columnas = de salida):

| coef \ salida | 5 | 6 | 7 | 8 | 9 |
|---:|---:|---:|---:|---:|---:|
| 5 | 29,8 | | | | |
| 6 | 32,6 | 42,1 | | | |
| **7** | 35,9 | 37,8 | **44,3** | | |
| 8 | 35,9 | 42,1 | 43,1 | 47,4 | |
| 9 | 36,0 | 43,4 | 50,2 | 50,3 | 57,6 |

Rama en frecuencia con coef = salida = 7, variando un nodo por vez:

| Bits fraccionarios | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---:|---:|---:|---:|---:|---:|
| `work` | 39,6 | **43,0** | 44,2 | 44,5 | 44,5 | 44,5 |
| W | 31,0 | 33,6 | 39,2 | 41,4 | **43,0** | 42,9 |
| H | 32,2 | 37,4 | 39,5 | 41,0 | **43,0** | 42,3 |

Con 6 bits fraccionarios en coeficientes y salida (salida de 8 bits) también se cumple, con 42,1/41,7 dB; se eligieron 7 para tener unos 3 dB de margen. **Resultado con el formato elegido:** tiempo **44,2 dB**, frecuencia **43,0 dB**; diferencia máxima entre ramas, 2 LSB. El error de los coeficientes domina, por eso agregar bits a `work` no mejora más allá de ~44,5 dB.

**Ejemplo de corte** (ejemplo 3 de abajo): `h_q[3] = round(0,68939 × 128) = 88`. Con x = −1 el producto es −88 (Q1.7 = −0,6875). Recortar a 2 bits fraccionarios: `(−88 + 16) >>> 5 = −3` (−0,75); `(−80 + 16) >>> 5 = −2`, porque −2,5 redondea hacia arriba. Sin saturación: si un valor no entra en su ancho, el modelo levanta `OverflowError` en lugar de envolver.

## Ejemplos obligatorios antes de aprobar

1. Una secuencia QPSK breve con los símbolos complejos y las muestras 2× exactas.
2. Tabla de los ocho coeficientes con precisión suficiente para reproducirla, la fórmula o script que la genera y la respuesta al impulso con índice de muestra.
3. Un ejemplo de multiplicación/acumulación en punto fijo que muestre signo, redondeo y saturación.
4. Archivo de configuración/semilla que regenere los vectores, y evidencia SQNR ≥ 40 dB con la definición acordada.

Al aprobar, copiar **solo los valores consumidos por código** a `config/project.json`. El modelo, RTL y testbench deben leer o derivar el mismo orden y escala.
