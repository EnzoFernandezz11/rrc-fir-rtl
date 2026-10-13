# Resultados y análisis PPA del filtro en frecuencia

Este es el registro común de las corridas **seriales y optimizadas**. Cada entrada
identifica variante, revisión, configuración, herramientas y evidencias. Las
nuevas medidas se agregan conservando las anteriores; las ejecuciones equivalentes
con el mismo diseño, configuración, herramientas, vector y resultados se registran una sola vez; las medidas de Vivado se
incorporan a la corrida correspondiente o como una entrada vinculada a su base local.

[Procedimiento de medición](../../docs/frecuencia/ppa.md) · [Diagramas RTL](../../docs/frecuencia/diagrams-rtl-modules-unitirarios.md)

<!-- serial-analysis:start -->
## Análisis base serial

Esta corrida establece la referencia del serial para decidir qué optimizar. La
comparación posterior será contra esta base, conservando FPGA, flujo, formatos,
vector y condiciones de medida; se declarará cualquier cambio de reloj. El
objetivo es mejorar throughput, área o energía por muestra con evidencia.

### Dónde se gastan los ciclos

El benchmark verifica **575 ciclos por bloque de ocho muestras**, con entrada
disponible y salida siempre lista. El desglose siguiente se deriva del calendario
del controlador actual; no son contadores independientes de cada fase:

| Trabajo por bloque | Cálculo | Ciclos | Fracción del bloque |
|---|---|---:|---:|
| FFT16 | 32 mariposas × 7 ciclos | 224 | 39,0 % |
| Productos espectrales | 16 bins × 6 ciclos | 96 | 16,7 % |
| Reordenamiento antes de IFFT | 6 intercambios | 6 | 1,0 % |
| IFFT16 | 32 mariposas × 7 ciclos | 224 | 39,0 % |
| Preparación, captura, emisión y transiciones externas al motor | 575 − 550 | 25 | 4,3 % |
| **Total** | **550 del motor + 25 externos** | **575** | **100 %** |

**El motor ocupa el 95,7 % del bloque; FFT e IFFT juntas, el 77,9 %.**
La primera hipótesis para mejorar throughput es reducir ciclos de las mariposas
y del multiplicador compartido. C03 debe estudiar el paralelismo de FFT,
productos e IFFT. El bypass de twiddles triviales puede complementar ese estudio,
manteniendo los cortes y redondeos A04. Reducir únicamente la preparación y la
emisión tiene poco alcance: incluso eliminar idealmente los 25 ciclos externos
daría como máximo 575/550 = **1,045×** throughput al mismo reloj. Es un límite
teórico, no una optimización medida.

El throughput de esta arquitectura es `8 × f_clk / 575`: a 10 MHz son
**139 130 muestras/s**. Bajar ciclos por bloque y subir el reloj son dos formas
distintas de mejorarlo. Cumplir timing a 10 MHz comprueba el mínimo del serial;
la Fmax estimada y el camino crítico indican el margen físico. La versión rápida
deberá implementarse y verificarse con su objetivo de al menos 100 MHz.

### Cómo decidir con los reportes de Vivado

| Pregunta | Evidencia que se debe leer | Decisión que permite tomar |
|---|---|---|
| ¿Cumple el reloj y dónde está el camino más lento? | WNS/WHS, `timing_critical.rpt`, diez caminos de `timing_setup.rpt` y `check_timing.rpt` | Registrar origen, destino, retardo de datos, niveles lógicos y reparto lógica/ruteo. Si predominan selectores, sumadores o acumulación, evaluar registros o simplificación en ese tramo; si predomina ruteo, revisar fanout y distribución. La ubicación concreta queda pendiente de esos reportes. |
| ¿Qué bloque consume LUT y FF? | `utilization_hierarchical.rpt` junto con `utilization.rpt` | Identificar los módulos dominantes y examinar sus bancos, multiplexores, ROM y control. Las filas padre incluyen descendientes: no sumarlas como recursos independientes. |
| ¿La memoria necesita otra implementación? | FF/LUT del motor, BRAM utilizada y accesos de `work_i/q` | El banco work tiene nominalmente 16 × 2 × 12 = 384 bits. Evaluar RAM solo si almacenamiento o selección dominan; sus puertos y escrituras simultáneas deben soportar las mariposas. Cero BRAM por sí solo no demuestra un problema. |
| ¿Conviene duplicar multiplicadores? | DSP del núcleo, ciclos de mariposas/bins, timing y energía | El serial comparte un multiplicador real. Más unidades pueden reducir ciclos, pero requieren medir LUT/FF/DSP, nuevo timing y energía antes de afirmar una mejora de PPA. |
| ¿Qué está gastando potencia? | Desglose por recurso/jerarquía disponible en `power.rpt`, `read_saif.rpt` y `unmatched_saif.rpt` | Buscar los componentes de mayor potencia dinámica y su actividad. Usar energía dinámica por muestra para evaluar el costo del paralelismo. Revisar cobertura SAIF antes de concluir; la estática reportada pertenece al dispositivo completo. |

La base ya pasa la comparación exacta de las 2048 salidas y verifica su calendario.
El mapeo local confirma un DSP y da recursos preliminares; la distribución física
por módulo, el cuello de botella de timing y la potencia requieren Vivado.
Un bloque que ocupa muchos ciclos no necesariamente contiene el camino crítico.

### Resultado que debe dejar la próxima issue

Antes de implementar C04, C03 debe registrar: **métrica a mejorar → evidencia de
la base → cambio propuesto → mejora esperada → costo esperado en recursos**.
Después se medirá la candidata contra esta corrida: ciclos/bloque, throughput,
latencia, WNS/Fmax, LUT/FF/DSP/BRAM y energía por muestra, verificando las mismas
salidas y SQNR ≥ 40 dB. Si cambia la aritmética, se deben justificar y verificar
los nuevos formatos y redondeos. Una predicción se mantendrá identificada como
tal hasta medirla.

<!-- serial-analysis:end -->

## Corridas seriales

<!-- serial-measurement:f6adf924bdc38769601ebc7b0a42d7b9eace1b154918537d5a0c7d97eedb5ac6 -->
### Frecuencia serial — corrida `20261013T220620013563Z-b9bd2183` (local)

**Estado: verificación local y mapeo lógico completados; PPA físico pendiente de Vivado.**

#### Configuración y trazabilidad

| Dato | Valor |
|---|---|
| Corrida UTC | `20261013T220620013563Z-b9bd2183` |
| Commit base | `b9bd2183af88fe8c5aec073f5ef5fc55143bc6ab` |
| Cambios locales al iniciar | Sí; consultar estado y hashes del manifiesto |
| Módulo | `fir_frequency_serial` completo |
| FPGA | Basys3 / Artix-7 `xc7a35tcpg236-1` |
| Reloj objetivo | 10 MHz / 100 ns |
| Implementación prevista | Out-of-context, estrategias por defecto |
| Formato | A04: entrada 2/F0, trabajo 12/F5, coeficientes 10/F8, salida 9/F7 |
| Estímulo | QPSK 2×, semilla 1, 1024 símbolos, 2048 muestras |
| Interfaz | Entrada disponible, salida siempre lista |
| Vectores | Modelo A04 local; formato común A05 pendiente |
| Yosys | `Yosys 0.52 (git sha1 fee39a3284c90249e1d9684cf6944ffbbcbb8f90)` |
| Icarus | `Icarus Verilog version 12.0 (stable) ()` |

#### Verificación y rendimiento funcional

Regresión `smoke` y comparación exacta de las 2048 salidas: **PASS**.
La simulación RTL usa 100 ns; la capacidad física de operar a ese período se comprueba en Vivado.

| Medición | Resultado |
|---|---|
| Muestras aceptadas / verificadas | 2048 / 2048 |
| Bloques completos | 256 |
| Latencia por muestra | 559 ciclos = 55.9 µs |
| Intervalo entre bloques (8 muestras) | 575 ciclos = 57.5 µs |
| Ventana de procesamiento, sin reset | 147200 ciclos = 14.72 ms |
| Throughput a 10 MHz | 139130.435 muestras/s |

#### Recursos preliminares — Yosys XC7

Conteo de primitivas del núcleo aplanado, sin buffers de entrada/salida ni de reloj.
Las LUT son la suma de LUT1…LUT6; no equivalen directamente a slices o CLB.

| Recurso | Cantidad |
|---|---|
| LUT | 1507 |
| FF | 610 |
| DSP48E1 | 1 |
| RAMB18E1 | 0 |
| RAMB36E1 | 0 |
| CARRY4 | 49 |
| MUXF7 | 189 |
| MUXF8 | 22 |

#### Resultados físicos — Vivado

| Métrica | Estado |
|---|---|
| LUT / FF / DSP / BRAM implementados | Pendiente |
| WNS a 100 ns / caminos sin constraints | Pendiente |
| Fmax aproximada de caminos internos | Pendiente |
| Simulación temporal y anotación SAIF | Pendiente |
| Potencia dinámica / estática | Pendiente |
| Energía dinámica por muestra | Pendiente |
| Versión Vivado / condiciones térmicas | Pendiente |

Se exige WNS ≥ 0 a 100 ns. La estimación de Fmax es `1000/(100 − WNS_ns)` MHz,
usando caminos internos de setup del mismo reloj; no reemplaza otra implementación a esa frecuencia.
Energía dinámica por muestra = potencia dinámica / throughput de la ventana SAIF.

El [análisis de la base serial](frequency.md#análisis-base-serial) reúne el desglose
de ciclos y los criterios para elegir la próxima optimización.

#### Evidencia

- Corrida: `build/ppa/frequency_serial/20261013T220620013563Z-b9bd2183/`.
- [Manifiesto y hashes](../../build/ppa/frequency_serial/20261013T220620013563Z-b9bd2183/manifest.json).
- [Métricas del benchmark](../../build/ppa/frequency_serial/20261013T220620013563Z-b9bd2183/local_metrics.json).
- [Recursos y primitivas](../../build/ppa/frequency_serial/20261013T220620013563Z-b9bd2183/resources.json).
- [Onda de los primeros cuatro bloques](../../build/ppa/frequency_serial/20261013T220620013563Z-b9bd2183/first_blocks.vcd).
- Logs: `build/ppa/frequency_serial/20261013T220620013563Z-b9bd2183/logs/`; incluyen regresión, compilación, simulación y síntesis.
- [Procedimiento local y Windows](../../docs/frecuencia/ppa.md).

Los archivos pesados y la copia original `summary.md` de esta corrida quedan en
`build/`. Los resultados de Vivado se incorporarán al registro común conservando
las corridas anteriores.

<!-- serial-runs:end -->

## Frecuencia optimizada

Pendiente de implementación y medición en C03/C04. Aquí se registrarán sus corridas, el análisis de resultados y la comparación con la base serial bajo condiciones declaradas.
