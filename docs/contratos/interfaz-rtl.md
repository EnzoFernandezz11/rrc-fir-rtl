# Contrato: interfaz RTL y temporización

**Estado:** Propuesto (E03, #4)
**Preparan:** @moreyrajulian y @EnzoFernandezz11
**Revisa:** @andres332271
**Issues:** E03, B01, C01, A06

Ambos filtros exponen la misma interfaz externa aunque sus latencias y tasas de aceptación difieran. Cada núcleo es una caja con un enlace de entrada y uno de salida; lo que pasa adentro (MAC, FFT, FSM, memorias) queda a cargo de B01/C01. Ningún puerto es definitivo hasta la revisión de @andres332271, @moreyrajulian y @EnzoFernandezz11.

La propuesta toma el handshake `valid/ready` con `last` del borrador de R01 (#31) y de C01, que coinciden. El reset se elige por la tecnología de [D05](verificacion-y-ppa.md#ppa): Vivado sobre FPGA Xilinx.

## Resumen

| Elemento | Definición propuesta | Motivo |
|---|---|---|
| `clk` y polaridad/tipo de reset | Un reloj `clk`, flanco ascendente. `rst` **síncrono, activo alto**. | Xilinx recomienda reset síncrono activo alto (UG949), y los registros internos de los DSP48 solo admiten reset síncrono: con reset asíncrono el multiplicador no puede absorber sus registros. C01 había elegido `rst_n` asíncrono bajo como decisión local; se reemplaza por este si se aprueba. |
| Ancho y signo de I/Q de entrada/salida | I y Q en puertos separados, `signed`, complemento a dos. Entrada `W_IN = 2`, `F_IN = 0` ({−1, 0, +1}, E02). Salida `W_OUT`/`F_OUT` como parámetros hasta que A04 los fije. | Evitar conversiones ocultas en testbench; valor real = entero / 2^F. |
| Aceptación de entrada | `in_valid` / `in_ready`: la muestra pasa en el flanco con `in_valid && in_ready`. | Una versión serial no acepta una muestra por ciclo. |
| Validez de salida y backpressure | `out_valid` / `out_ready`, con la misma regla. El núcleo sostiene la salida mientras `out_ready = 0`. | Asociar cada salida a su muestra sin perder ni duplicar. |
| Inicio/fin de bloque en frecuencia | `in_last` acompaña a la última muestra de la trama; `out_last`, al último resultado. Los bloques FFT son internos al núcleo. | Misma interfaz para un flujo temporal y uno por bloques. |
| Orden de I/Q y primera muestra válida | La primera transferencia aceptada después del reset o de un `last` es `x[0]` de una trama nueva, con historial cero. Los resultados salen en orden `y[0], y[1], …`. | Vector matching por índice, sin desplazamientos arbitrarios. |
| Comportamiento ante reset y burbujas | Ver [Reglas por ciclo](#reglas-por-ciclo). Una burbuja (`valid = 0`) no es una muestra; un cero con `valid = 1` sí lo es. | Pruebas de protocolo. |
| Latencia en ciclos/throughput por variante | Cada variante declara `L` e `II` (definidos abajo) y los mide en su testbench. | Comparación PPA. |

## Puertos del núcleo

Iguales para las cuatro variantes. Los nombres de módulo los eligen B02/C02/B04/C04.

| Puerto | Dirección | Tipo | Descripción |
|---|---|---|---|
| `clk` | entrada | 1 bit | Reloj, flanco ascendente. |
| `rst` | entrada | 1 bit | Reset síncrono activo alto. |
| `in_i`, `in_q` | entrada | `signed [W_IN-1:0]` | Muestra de entrada `x[n]`. |
| `in_valid` | entrada | 1 bit | Hay una muestra presentada. |
| `in_last` | entrada | 1 bit | La muestra presentada es la última de la trama. |
| `in_ready` | salida | 1 bit | El núcleo puede aceptar una muestra en este flanco. |
| `out_i`, `out_q` | salida | `signed [W_OUT-1:0]` | Resultado `y[n]`, ya en el formato externo. |
| `out_valid` | salida | 1 bit | Hay un resultado presentado. |
| `out_last` | salida | 1 bit | El resultado presentado es el último de la trama. |
| `out_ready` | entrada | 1 bit | El receptor acepta el resultado en este flanco. |

| Parámetro | Valor | Fuente |
|---|---|---|
| `W_IN`, `F_IN` | 2, 0 | E02 ([señales y formatos](senales-y-formatos.md)) |
| `W_OUT`, `F_OUT` | Por definir | A04 |

## Reglas por ciclo

1. **Transferencia.** Un dato `{i, q, last}` pasa en el flanco ascendente en que `valid && ready` y `rst = 0`. Datos y `last` no tienen significado con `valid = 0`.
2. **Sostener.** Si `valid = 1` y `ready = 0`, el productor mantiene `valid`, I/Q y `last` sin cambios hasta la transferencia o el reset.
3. **Sin dependencia circular.** `valid` no depende de `ready`: el productor anuncia el dato sin esperar `ready`. El receptor sí puede mirar `valid` para decidir `ready`, pero el núcleo no debe tener un camino combinacional de `in_valid` a `in_ready` ni de `out_ready` a `out_valid`.
4. **Conteo.** Por cada muestra aceptada `x[n]` el núcleo entrega exactamente un resultado `y[n] = Σ h[k]·x[n−k]`, con `x[n<0] = 0` dentro de la trama. Una trama de N muestras produce N resultados, sin cola. Con 2× y S símbolos, N = 2S.
5. **Trama.** `out_last = 1` solo en el resultado de la muestra que llegó con `in_last = 1`. Después de aceptar `in_last`, el núcleo puede mantener `in_ready = 0` hasta entregar el último resultado y dejar el historial en cero; la siguiente muestra aceptada es `x[0]` de una trama independiente. Una trama vacía no genera transferencias.
6. **Reset.** Con `rst = 1` no hay transferencias: el núcleo pone `in_ready = 0` y `out_valid = 0`, vacía el historial, cancela resultados pendientes y vuelve al estado de inicio. En el primer flanco con `rst = 0` puede volver a aceptar.
7. **Burbujas.** Un ciclo con `in_valid = 0` no avanza ningún índice ni modifica el historial. Las pausas de entrada o salida solo alargan el tiempo, nunca cambian los valores.

## Latencia y throughput

Cada variante documenta en su PR y mide en su testbench, con entrada siempre disponible y `out_ready = 1`:

| Símbolo | Definición |
|---|---|
| `L` | Ciclos desde el flanco que acepta `x[n]` hasta el primer flanco con `out_valid = 1` para `y[n]`, en régimen. Para frecuencia se declara la del peor índice del bloque. |
| `II` | Intervalo de inicio: ciclos entre dos aceptaciones consecutivas en régimen. `II = 1` acepta una muestra por ciclo. |
| Throughput | `f_clk / II` muestras por segundo. Frecuencia, que trabaja por bloques, declara su promedio: `8 · f_clk / ciclos_por_bloque`. |

El banco de pruebas compara por **índice de resultado aceptado**, no por ciclo de reloj: el k-ésimo resultado aceptado después del inicio de la trama se compara con `y[k]` del modelo.

## Ejemplo de secuencia

Protocolo ilustrativo, no arquitectura: un núcleo hipotético con `II = 3` y `L = 2`. Los valores reales de cada variante los fijan B01 y C01, que agregan aquí su propia tabla. `↑` marca una transferencia.

| Ciclo | `rst` | `in_valid` | `in_ready` | Entrada | `out_valid` | `out_ready` | Salida | Qué pasa |
|---:|:-:|:-:|:-:|---|:-:|:-:|---|---|
| 0 | 1 | 0 | 0 | — | 0 | 1 | — | Reset: no hay transferencias. |
| 1 | 0 | 1 | 1 | `x[0]` ↑ | 0 | 1 | — | Primera muestra aceptada. |
| 2 | 0 | 1 | 0 | `x[1]` | 0 | 1 | — | Núcleo ocupado: el productor sostiene `x[1]`. |
| 3 | 0 | 1 | 0 | `x[1]` | 1 | 0 | `y[0]` | `y[0]` listo, pero el receptor no acepta: se sostiene. |
| 4 | 0 | 1 | 1 | `x[1]` ↑ | 1 | 1 | `y[0]` ↑ | Se aceptan `x[1]` y `y[0]` en el mismo flanco. |
| 5 | 0 | 0 | 0 | — | 0 | 1 | — | Burbuja de entrada: no cuenta como muestra. |
| 6 | 0 | 0 | 0 | — | 1 | 1 | `y[1]` ↑ | `y[1]` sale aunque la entrada esté en pausa. |
| 7 | 0 | 1 | 1 | `x[2]`, `last` ↑ | 0 | 1 | — | Última muestra de la trama: `0` válido del 2×. |
| 8 | 0 | 0 | 0 | — | 0 | 1 | — | `in_ready = 0` hasta cerrar la trama. |
| 9 | 0 | 0 | 0 | — | 1 | 1 | `y[2]`, `last` ↑ | Fin de trama; el historial vuelve a cero. |
| 10 | 0 | 1 | 1 | `x[0]` ↑ | 0 | 1 | — | Primera muestra de una trama nueva. |

## Revisión

- [ ] @andres332271 puede escribir un testbench común sin conocer la FSM interna.
- [ ] @moreyrajulian y @EnzoFernandezz11 confirman que sus arquitecturas pueden cumplir la interfaz.
- [ ] El contrato precisa qué ocurre si llega una entrada mientras el diseño no está listo (reglas 2 y 5).
