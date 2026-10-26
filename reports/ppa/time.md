# Resultados PPA temporales: B02 y B04

> **Regla obligatoria de mantenimiento:** mostrar únicamente la **última corrida exitosa de cada variante**. Una nueva corrida reemplaza íntegramente su sección, incluso si reproduce los mismos valores; no se agregan históricos ni resúmenes duplicados. Cada resultado debe enlazar configuración, biblioteca, hashes y logs. Las corridas anteriores permanecen en `build/ppa/`. Una corrida fallida no reemplaza resultados válidos.

Medición: **ASIC SKY130 HD, 130 nm, TT / 25 °C / 1,8 V**, con el mismo flujo que
las variantes de frecuencia (C02/C04): síntesis Yosys y, en la etapa física,
OpenLane 2 hasta STA post-ruteo con SPEF y potencia con actividad VCD. Los
objetivos son 10 MHz (100 ns) para B02 y 100 MHz (10 ns) para B04; sólo una
corrida física con timing PASS demuestra que se alcanzan.

[Procedimiento y comandos](../../docs/ppa-tiempo.md).

## Última corrida B02 — tiempo serial

<!-- serial-runs:start -->

<!-- serial-measurement:c6c8a241113a8a07fb31da763f59a428083649568eb342ef4792e5d42485f071 -->
### time_serial — corrida 20261026T232806297309Z-56822367 (OpenLane 2 / SKY130)

**Medición física completa; simulación funcional de netlist final, STA post-SPEF y potencia con VCD.**

Potencia estimada TT/25 °C/1,8 V, sin retardos de simulación ni glitches temporales completos. No es signoff de fabricación.

| Escenario | Reloj | Setup/hold | Restricciones eléctricas | Timing global | Potencia total | Energía total/muestra |
|---|---:|---|---|---|---:|---:|
| target | 10 MHz | PASS | FAIL | FAIL | 8.68215534e-05 W | 8.68215534e-11 J |
| common | 10 MHz | PASS | FAIL | FAIL | 8.68215534e-05 W | 8.68215534e-11 J |

#### Área y benchmark

| Medición | Resultado |
|---|---:|
| Área final de celdas | 4748.300 µm² |
| Área del core | 11272.061 µm² |
| Área del die | 15064.621 µm² |
| Latencia | 9 ciclos |
| Intervalo entre muestras (II) | 10 ciclos |
| Ciclos activos | 20480 ciclos |
| Throughput efectivo (condicionado; timing global FAIL) | 1000000.000 muestras/s |
| Throughput sostenido (condicionado; timing global FAIL) | 1000000.000 muestras/s |

El throughput al reloj objetivo queda condicionado a PASS global de timing. Fmax es estimación registro a registro, sin barrido.

#### Potencia y energía

| Escenario | Interna (W) | Switching (W) | Dinámica (W) | Leakage (W) | Total (W) | Energía dinámica/muestra (J) | Energía total/muestra (J) |
|---|---:|---:|---:|---:|---:|---:|---:|
| target | 5.87349225e-05 | 2.80831775e-05 | 8.68181e-05 | 3.45368006e-09 | 8.68215534e-05 | 8.68181e-11 | 8.68215534e-11 |
| common | 5.87349225e-05 | 2.80831775e-05 | 8.68181e-05 | 3.45368006e-09 | 8.68215534e-05 | 8.68181e-11 | 8.68215534e-11 |

#### Timing por corner

| Escenario | Corner | Setup WS (ns) | Hold WS (ns) | Setup/hold violaciones | Slew / cap / fanout violaciones | Fmax estimada (MHz) |
|---|---|---:|---:|---:|---:|---:|
| target | nom_tt_025C_1v80 | 58.7977 | 0.3547 | 0 / 0 | 0 / 0 / 1 | 240.97 |
| target | nom_ss_100C_1v60 | 57.9945 | 0.9535 | 0 / 0 | 0 / 0 / 1 | 125.64 |
| target | nom_ff_n40C_1v95 | 59.1157 | 0.1097 | 0 / 0 | 0 / 0 / 1 | 380.76 |
| target | min_tt_025C_1v80 | 58.8166 | 0.3504 | 0 / 0 | 0 / 0 / 1 | 243.17 |
| target | min_ss_100C_1v60 | 58.0264 | 0.9477 | 0 / 0 | 0 / 0 / 1 | 126.71 |
| target | min_ff_n40C_1v95 | 59.1276 | 0.1084 | 0 / 0 | 0 / 0 / 1 | 386.77 |
| target | max_tt_025C_1v80 | 58.7794 | 0.3573 | 0 / 0 | 0 / 0 / 1 | 238.74 |
| target | max_ss_100C_1v60 | 57.9635 | 0.9569 | 0 / 0 | 0 / 0 / 1 | 124.54 |
| target | max_ff_n40C_1v95 | 59.1039 | 0.1114 | 0 / 0 | 0 / 0 / 1 | 375.00 |
| common | nom_tt_025C_1v80 | 58.7977 | 0.3547 | 0 / 0 | 0 / 0 / 1 | 240.97 |
| common | nom_ss_100C_1v60 | 57.9945 | 0.9535 | 0 / 0 | 0 / 0 / 1 | 125.64 |
| common | nom_ff_n40C_1v95 | 59.1157 | 0.1097 | 0 / 0 | 0 / 0 / 1 | 380.76 |
| common | min_tt_025C_1v80 | 58.8166 | 0.3504 | 0 / 0 | 0 / 0 / 1 | 243.17 |
| common | min_ss_100C_1v60 | 58.0264 | 0.9477 | 0 / 0 | 0 / 0 / 1 | 126.71 |
| common | min_ff_n40C_1v95 | 59.1276 | 0.1084 | 0 / 0 | 0 / 0 / 1 | 386.77 |
| common | max_tt_025C_1v80 | 58.7794 | 0.3573 | 0 / 0 | 0 / 0 / 1 | 238.74 |
| common | max_ss_100C_1v60 | 57.9635 | 0.9569 | 0 / 0 | 0 / 0 / 1 | 124.54 |
| common | max_ff_n40C_1v95 | 59.1039 | 0.1114 | 0 / 0 | 0 / 0 / 1 | 375.00 |
- [manifest.json](time_serial/sky130/manifest.json).
- [physical_metrics.json](time_serial/sky130/physical_metrics.json).
- [local_metrics.json](time_serial/sky130/local_metrics.json).
- [gate_metrics.json](time_serial/sky130/gate_metrics.json).
- [resources.json](time_serial/sky130/resources.json).
- [openlane-target.json](time_serial/sky130/openlane-target.json).
- [Reportes STA por corner](time_serial/sky130/runs/).
El escenario common comparte la corrida target al mismo reloj; no se creó un directorio adicional.
- [Actividad y potencia target](time_serial/sky130/target/) y [Actividad y potencia common](time_serial/sky130/target/).
- Los directorios de escenario existentes conservan `power.sdc` y el log combinado `power.log`.

<!-- serial-runs:end -->

## Última corrida B04 — tiempo optimizada

<!-- optimized-runs:start -->

<!-- optimized-measurement:ac51ec4ceb9da8af3c4a846b6144e0d06ecc56fea53c4ffff50b85fb31115674 -->
### time_optimized — corrida 20261026T232043947866Z-56822367 (OpenLane 2 / SKY130)

**Medición física completa; simulación funcional de netlist final, STA post-SPEF y potencia con VCD.**

Potencia estimada TT/25 °C/1,8 V, sin retardos de simulación ni glitches temporales completos. No es signoff de fabricación.

| Escenario | Reloj | Setup/hold | Restricciones eléctricas | Timing global | Potencia total | Energía total/muestra |
|---|---:|---|---|---|---:|---:|
| target | 100 MHz | PASS | FAIL | FAIL | 0.00223322191 W | 2.23431235e-11 J |
| common | 10 MHz | PASS | FAIL | FAIL | 0.000223326948 W | 2.23435994e-11 J |

#### Área y benchmark

| Medición | Resultado |
|---|---:|
| Área final de celdas | 8413.070 µm² |
| Área del core | 19526.227 µm² |
| Área del die | 24749.179 µm² |
| Latencia | 1 ciclos |
| Intervalo entre muestras (II) | 1 ciclos |
| Ciclos activos | 2049 ciclos |
| Throughput efectivo (condicionado; timing global FAIL) | 99951195.705 muestras/s |
| Throughput sostenido (condicionado; timing global FAIL) | 100000000.000 muestras/s |

El throughput al reloj objetivo queda condicionado a PASS global de timing. Fmax es estimación registro a registro, sin barrido.

#### Potencia y energía

| Escenario | Interna (W) | Switching (W) | Dinámica (W) | Leakage (W) | Total (W) | Energía dinámica/muestra (J) | Energía total/muestra (J) |
|---|---:|---:|---:|---:|---:|---:|---:|
| target | 0.00154675584 | 0.000686460857 | 0.00223321669 | 5.23352794e-09 | 0.00223322191 | 2.23430713e-11 | 2.23431235e-11 |
| common | 0.000154675597 | 6.86461172e-05 | 0.000223321714 | 5.23352794e-09 | 0.000223326948 | 2.23430758e-11 | 2.23435994e-11 |

#### Timing por corner

| Escenario | Corner | Setup WS (ns) | Hold WS (ns) | Setup/hold violaciones | Slew / cap / fanout violaciones | Fmax estimada (MHz) |
|---|---|---:|---:|---:|---:|---:|
| target | nom_tt_025C_1v80 | 5.0613 | 0.3382 | 0 / 0 | 0 / 0 / 1 | 322.22 |
| target | nom_ss_100C_1v60 | 2.3263 | 0.9461 | 0 / 0 | 0 / 0 / 1 | 173.47 |
| target | nom_ff_n40C_1v95 | 5.2922 | 0.1127 | 0 / 0 | 0 / 0 / 1 | 469.39 |
| target | min_tt_025C_1v80 | 5.0688 | 0.3346 | 0 / 0 | 0 / 0 / 1 | 329.75 |
| target | min_ss_100C_1v60 | 2.3904 | 0.9396 | 0 / 0 | 0 / 0 / 1 | 175.08 |
| target | min_ff_n40C_1v95 | 5.2971 | 0.1102 | 0 / 0 | 0 / 0 / 1 | 479.91 |
| target | max_tt_025C_1v80 | 5.0522 | 0.3413 | 0 / 0 | 0 / 0 / 1 | 315.54 |
| target | max_ss_100C_1v60 | 2.2669 | 0.9531 | 0 / 0 | 0 / 0 / 1 | 170.24 |
| target | max_ff_n40C_1v95 | 5.2862 | 0.1149 | 0 / 0 | 0 / 0 / 1 | 460.22 |
| common | nom_tt_025C_1v80 | 59.0613 | 0.3382 | 0 / 0 | 0 / 0 / 1 | 322.22 |
| common | nom_ss_100C_1v60 | 58.4585 | 0.9461 | 0 / 0 | 0 / 0 / 1 | 173.47 |
| common | nom_ff_n40C_1v95 | 59.2922 | 0.1127 | 0 / 0 | 0 / 0 / 1 | 469.39 |
| common | min_tt_025C_1v80 | 59.0688 | 0.3346 | 0 / 0 | 0 / 0 / 1 | 329.75 |
| common | min_ss_100C_1v60 | 58.4685 | 0.9396 | 0 / 0 | 0 / 0 / 1 | 175.08 |
| common | min_ff_n40C_1v95 | 59.2971 | 0.1102 | 0 / 0 | 0 / 0 / 1 | 479.91 |
| common | max_tt_025C_1v80 | 59.0522 | 0.3413 | 0 / 0 | 0 / 0 / 1 | 315.54 |
| common | max_ss_100C_1v60 | 58.4426 | 0.9531 | 0 / 0 | 0 / 0 / 1 | 170.24 |
| common | max_ff_n40C_1v95 | 59.2862 | 0.1149 | 0 / 0 | 0 / 0 / 1 | 460.22 |
- [manifest.json](time_optimized/sky130/manifest.json).
- [physical_metrics.json](time_optimized/sky130/physical_metrics.json).
- [local_metrics.json](time_optimized/sky130/local_metrics.json).
- [gate_metrics.json](time_optimized/sky130/gate_metrics.json).
- [resources.json](time_optimized/sky130/resources.json).
- [openlane-target.json](time_optimized/sky130/openlane-target.json).
- [openlane-common.json](time_optimized/sky130/openlane-common.json).
- [Reportes STA por corner](time_optimized/sky130/runs/).
- [Actividad y potencia target](time_optimized/sky130/target/) y [Actividad y potencia common](time_optimized/sky130/common/).
- Los directorios de escenario existentes conservan `power.sdc` y el log combinado `power.log`.

<!-- optimized-runs:end -->

<!-- comparison:start -->

## Comparación B02 / B04

Corridas: [B02](time_serial/sky130/manifest.json) / [B04](time_optimized/sky130/manifest.json). Benchmark: QPSK 2×, semilla 1, 2048 muestras exactas.

Las diferencias porcentuales son (B04/B02 − 1) × 100; un signo positivo no siempre significa mejora.

Medición física; revisar PASS/FAIL por corner antes de interpretar las tasas.

| Métrica | Unidad | B02 | B04 | Cambio B04/B02 | Condición / procedencia |
|---|---|---:|---:|---:|---|
| Muestras aceptadas | muestras | 2048 | 2048 | 0 % | local_metrics.json / resources.json |
| Muestras exactas | muestras | 2048 | 2048 | 0 % | local_metrics.json / resources.json |
| Reloj configurado | MHz | 10 | 100 | 900 % | Objetivos propios, 10/100 MHz; hipotético si timing FAIL |
| Latencia | ciclos | 9 | 1 | -88.888889 % | local_metrics.json / resources.json |
| Intervalo entre muestras (II) | ciclos | 10 | 1 | -90 % | local_metrics.json / resources.json |
| Ciclos activos del benchmark | ciclos | 20480 | 2049 | -89.995117 % | local_metrics.json / resources.json |
| Latencia temporal | ns | 900 | 10 | -98.888889 % | Objetivos propios, 10/100 MHz; hipotético si timing FAIL |
| Throughput sostenido | muestras/s | 1000000 | 1e+08 | 9900 % | Objetivos propios, 10/100 MHz; hipotético si timing FAIL |
| Throughput efectivo | muestras/s | 1000000 | 9.99512e+07 | 9895.119571 % | Objetivos propios, 10/100 MHz; hipotético si timing FAIL |
| Celdas de síntesis | celdas | 396 | 779 | 96.717172 % | local_metrics.json / resources.json |
| Flip-flops de síntesis | FF | 63 | 132 | 109.52381 % | local_metrics.json / resources.json |
| Celdas combinacionales de síntesis | celdas | 333 | 647 | 94.294294 % | local_metrics.json / resources.json |
| Área de celdas de síntesis | µm² | 3298.1632 | 6459.9456 | 95.864947 % | local_metrics.json / resources.json |
| Área final de celdas | µm² | 4748.3 | 8413.07 | 77.180675 % | physical_metrics.json |
| Área del núcleo | µm² | 11272.0608 | 19526.2272 | 73.226773 % | physical_metrics.json |
| Área del die | µm² | 15064.621425 | 24749.1785 | 64.28676 % | physical_metrics.json |
| Potencia interna | W | 5.87349e-05 | 0.001547 | 2533.451738 % | Netlist final / SPEF / VCD, TT; objetivos propios |
| Potencia de conmutación | W | 2.80832e-05 | 0.000686461 | 2344.384566 % | Netlist final / SPEF / VCD, TT; objetivos propios |
| Potencia dinámica | W | 8.68181e-05 | 0.002233 | 2472.293904 % | Netlist final / SPEF / VCD, TT; objetivos propios |
| Leakage del núcleo | W | 3.45368e-09 | 5.23353e-09 | 51.534822 % | Netlist final / SPEF / VCD, TT; objetivos propios |
| Potencia total | W | 8.68216e-05 | 0.002233 | 2472.197594 % | Netlist final / SPEF / VCD, TT; objetivos propios |
| Energía dinámica por muestra | J/muestra | 8.68181e-11 | 2.23431e-11 | -74.264501 % | Netlist final / SPEF / VCD, TT; objetivos propios |
| Energía total por muestra | J/muestra | 8.68216e-11 | 2.23431e-11 | -74.265465 % | Netlist final / SPEF / VCD, TT; objetivos propios |
| Pines con actividad VCD/reloj/constante | % | 100 | 100 | 0 % | physical_metrics.json |

### Radares normalizados

100 es el mejor valor **de esta pareja** en cada eje. Más afuera es mejor. Beneficios: 100 × valor/máximo; costos: 100 × mínimo/valor. Empate en cero: ambos 100; costo cero frente a costo positivo: 100 frente a 0. La superficie no es una puntuación global. Valores originales en la tabla.

```mermaid
---
config:
  theme: base
  themeVariables:
    cScale0: '#2563eb'
    cScale1: '#ea580c'
    fontSize: 18px
    radar:
      curveOpacity: 0.25
      axisLabelFontSize: 16px
      legendFontSize: 16px
  radar:
    width: 900
    height: 700
    axisScaleFactor: 1
    marginTop: 60
    marginBottom: 60
    marginLeft: 100
    marginRight: 100
    curveTension: 0
---
radar-beta
    title Arquitectura y síntesis
    axis a0["Área síntesis"], a1["FF"], a2["Latencia"], a3["II"]
    curve b02["B02"]{100.00000, 100.00000, 11.11111, 10.00000}
    curve b04["B04"]{51.05559, 47.72727, 100.00000, 100.00000}
    min 0
    max 100
    ticks 5
    showLegend true
```

[Fuente Mermaid](time_comparison/radar-arquitectura.mmd)

### Barras: objetivos propios

Cada gráfico usa una unidad; menor costo favorece la variante más pequeña.

```mermaid
xychart-beta
    title "Latencia"
    x-axis ["B02", "B04"]
    y-axis "ciclos" 0.000000000000 --> 9.450000000000
    bar [9.000000000000, 1.000000000000]
```

[Fuente Mermaid](time_comparison/latency_cycles.mmd)

| ciclos | B02 | B04 |
|---|---:|---:|
| Latencia | 9 | 1 |

```mermaid
xychart-beta
    title "Intervalo entre muestras (II)"
    x-axis ["B02", "B04"]
    y-axis "ciclos" 0.000000000000 --> 10.500000000000
    bar [10.000000000000, 1.000000000000]
```

[Fuente Mermaid](time_comparison/block_cycles.mmd)

| ciclos | B02 | B04 |
|---|---:|---:|
| Intervalo entre muestras (II) | 10 | 1 |

```mermaid
xychart-beta
    title "Ciclos activos del benchmark"
    x-axis ["B02", "B04"]
    y-axis "ciclos" 0.000000000000 --> 21504.000000000000
    bar [20480.000000000000, 2049.000000000000]
```

[Fuente Mermaid](time_comparison/active_cycles.mmd)

| ciclos | B02 | B04 |
|---|---:|---:|
| Ciclos activos del benchmark | 20480 | 2049 |

```mermaid
xychart-beta
    title "Latencia temporal"
    x-axis ["B02", "B04"]
    y-axis "ns" 0.000000000000 --> 945.000000000000
    bar [900.000000000000, 10.000000000000]
```

[Fuente Mermaid](time_comparison/latency_ns.mmd)

| ns | B02 | B04 |
|---|---:|---:|
| Latencia temporal | 900 | 10 |

```mermaid
xychart-beta
    title "Throughput sostenido"
    x-axis ["B02", "B04"]
    y-axis "muestras/s" 0.000000000000 --> 105000000.000000000000
    bar [1000000.000000000000, 100000000.000000000000]
```

[Fuente Mermaid](time_comparison/sustained_sps.mmd)

| muestras/s | B02 | B04 |
|---|---:|---:|
| Throughput sostenido | 1000000 | 1e+08 |

```mermaid
xychart-beta
    title "Throughput efectivo"
    x-axis ["B02", "B04"]
    y-axis "muestras/s" 0.000000000000 --> 104948755.490483164787
    bar [1000000.000000000000, 99951195.705222055316]
```

[Fuente Mermaid](time_comparison/effective_sps.mmd)

| muestras/s | B02 | B04 |
|---|---:|---:|
| Throughput efectivo | 1000000 | 9.99512e+07 |

```mermaid
xychart-beta
    title "Celdas de síntesis"
    x-axis ["B02", "B04"]
    y-axis "celdas" 0.000000000000 --> 817.950000000000
    bar [396.000000000000, 779.000000000000]
```

[Fuente Mermaid](time_comparison/cells.mmd)

| celdas | B02 | B04 |
|---|---:|---:|
| Celdas de síntesis | 396 | 779 |

```mermaid
xychart-beta
    title "Flip-flops de síntesis"
    x-axis ["B02", "B04"]
    y-axis "FF" 0.000000000000 --> 138.600000000000
    bar [63.000000000000, 132.000000000000]
```

[Fuente Mermaid](time_comparison/flip_flops.mmd)

| FF | B02 | B04 |
|---|---:|---:|
| Flip-flops de síntesis | 63 | 132 |

```mermaid
xychart-beta
    title "Celdas combinacionales de síntesis"
    x-axis ["B02", "B04"]
    y-axis "celdas" 0.000000000000 --> 679.350000000000
    bar [333.000000000000, 647.000000000000]
```

[Fuente Mermaid](time_comparison/combinational_cells.mmd)

| celdas | B02 | B04 |
|---|---:|---:|
| Celdas combinacionales de síntesis | 333 | 647 |

```mermaid
xychart-beta
    title "Área de celdas de síntesis"
    x-axis ["B02", "B04"]
    y-axis "µm²" 0.000000000000 --> 6782.942880000001
    bar [3298.163200000000, 6459.945600000000]
```

[Fuente Mermaid](time_comparison/cell_area_um2.mmd)

| µm² | B02 | B04 |
|---|---:|---:|
| Área de celdas de síntesis | 3298.1632 | 6459.9456 |

```mermaid
xychart-beta
    title "Área final de celdas"
    x-axis ["B02", "B04"]
    y-axis "µm²" 0.000000000000 --> 8833.723500000000
    bar [4748.300000000000, 8413.070000000000]
```

[Fuente Mermaid](time_comparison/final_cell_area_um2.mmd)

| µm² | B02 | B04 |
|---|---:|---:|
| Área final de celdas | 4748.3 | 8413.07 |

```mermaid
xychart-beta
    title "Área del núcleo"
    x-axis ["B02", "B04"]
    y-axis "µm²" 0.000000000000 --> 20502.538559999997
    bar [11272.060800000001, 19526.227199999998]
```

[Fuente Mermaid](time_comparison/core_area_um2.mmd)

| µm² | B02 | B04 |
|---|---:|---:|
| Área del núcleo | 11272.0608 | 19526.2272 |

```mermaid
xychart-beta
    title "Área del die"
    x-axis ["B02", "B04"]
    y-axis "µm²" 0.000000000000 --> 25986.637425000004
    bar [15064.621425000001, 24749.178500000002]
```

[Fuente Mermaid](time_comparison/die_area_um2.mmd)

| µm² | B02 | B04 |
|---|---:|---:|
| Área del die | 15064.621425 | 24749.1785 |

```mermaid
xychart-beta
    title "Potencia interna"
    x-axis ["B02", "B04"]
    y-axis "mW" 0.000000000000 --> 1.624093629431
    bar [0.058734922504, 1.546755837553]
```

[Fuente Mermaid](time_comparison/internal_w.mmd)

| W | B02 | B04 |
|---|---:|---:|
| Potencia interna | 5.87349e-05 | 0.001547 |

```mermaid
xychart-beta
    title "Potencia de conmutación"
    x-axis ["B02", "B04"]
    y-axis "mW" 0.000000000000 --> 0.720783900213
    bar [0.028083177540, 0.686460857346]
```

[Fuente Mermaid](time_comparison/switching_w.mmd)

| W | B02 | B04 |
|---|---:|---:|
| Potencia de conmutación | 2.80832e-05 | 0.000686461 |

```mermaid
xychart-beta
    title "Potencia dinámica"
    x-axis ["B02", "B04"]
    y-axis "mW" 0.000000000000 --> 2.344877529644
    bar [0.086818100044, 2.233216694899]
```

[Fuente Mermaid](time_comparison/dynamic_w.mmd)

| W | B02 | B04 |
|---|---:|---:|
| Potencia dinámica | 8.68181e-05 | 0.002233 |

```mermaid
xychart-beta
    title "Leakage del núcleo"
    x-axis ["B02", "B04"]
    y-axis "mW" 0.000000000000 --> 0.000005495204
    bar [0.000003453680, 0.000005233528]
```

[Fuente Mermaid](time_comparison/leakage_w.mmd)

| W | B02 | B04 |
|---|---:|---:|
| Leakage del núcleo | 3.45368e-09 | 5.23353e-09 |

```mermaid
xychart-beta
    title "Potencia total"
    x-axis ["B02", "B04"]
    y-axis "mW" 0.000000000000 --> 2.344883002677
    bar [0.086821553396, 2.233221907311]
```

[Fuente Mermaid](time_comparison/total_w.mmd)

| W | B02 | B04 |
|---|---:|---:|
| Potencia total | 8.68216e-05 | 0.002233 |

```mermaid
xychart-beta
    title "Energía dinámica por muestra"
    x-axis ["B02", "B04"]
    y-axis "nJ/muestra" 0.000000000000 --> 0.091159005046
    bar [0.086818100044, 0.022343071327]
```

[Fuente Mermaid](time_comparison/dynamic_energy_j.mmd)

| J/muestra | B02 | B04 |
|---|---:|---:|
| Energía dinámica por muestra | 8.68181e-11 | 2.23431e-11 |

```mermaid
xychart-beta
    title "Energía total por muestra"
    x-axis ["B02", "B04"]
    y-axis "nJ/muestra" 0.000000000000 --> 0.091162631065
    bar [0.086821553396, 0.022343123477]
```

[Fuente Mermaid](time_comparison/total_energy_j.mmd)

| J/muestra | B02 | B04 |
|---|---:|---:|
| Energía total por muestra | 8.68216e-11 | 2.23431e-11 |

```mermaid
xychart-beta
    title "Pines con actividad VCD/reloj/constante"
    x-axis ["B02", "B04"]
    y-axis "%" 0.000000000000 --> 105.000000000000
    bar [100.000000000000, 100.000000000000]
```

[Fuente Mermaid](time_comparison/activity_coverage_pct.mmd)

| % | B02 | B04 |
|---|---:|---:|
| Pines con actividad VCD/reloj/constante | 100 | 100 |

### Reloj común: 10 MHz

Potencia común medida por variante (TT/25 °C/1,8 V), aunque el estado global no habilite gráficas:

| Métrica | Unidad | B02 | B04 |
|---|---|---:|---:|
| internal_w | W | 5.87349e-05 | 0.000154676 |
| switching_w | W | 2.80832e-05 | 6.86461e-05 |
| dynamic_w | W | 8.68181e-05 | 0.000223322 |
| leakage_w | W | 3.45368e-09 | 5.23353e-09 |
| total_w | W | 8.68216e-05 | 0.000223327 |
| dynamic_energy_j | J/muestra | 8.68181e-11 | 2.23431e-11 |
| total_energy_j | J/muestra | 8.68216e-11 | 2.23436e-11 |
Pendiente: ambas implementaciones deben demostrar timing a 10 MHz. No se grafican datos físicos supuestos.

### Timing por corner


Escenario target: B02 setup/hold **PASS**, eléctrico/restricciones **FAIL**, global **FAIL**; B04 setup/hold **PASS**, eléctrico/restricciones **FAIL**, global **FAIL**.

| Estado | B02 | B04 |
|---|---|---|
| Setup/hold | PASS | PASS |
| Eléctrico/restricciones | FAIL | FAIL |
| Global | FAIL | FAIL |

| Corner | Métrica | B02 | B04 |
|---|---|---:|---:|
| nom_tt_025C_1v80 | setup_ws_ns | 58.797697 | 5.061288 |
| nom_tt_025C_1v80 | hold_ws_ns | 0.354654 | 0.338199 |
| nom_tt_025C_1v80 | setup_wns_ns | 0 | 0 |
| nom_tt_025C_1v80 | hold_wns_ns | 0 | 0 |
| nom_tt_025C_1v80 | setup_tns_ns | 0 | 0 |
| nom_tt_025C_1v80 | hold_tns_ns | 0 | 0 |
| nom_tt_025C_1v80 | setup_violations | 0 | 0 |
| nom_tt_025C_1v80 | hold_violations | 0 | 0 |
| nom_tt_025C_1v80 | max_slew_violations | 0 | 0 |
| nom_tt_025C_1v80 | max_cap_violations | 0 | 0 |
| nom_tt_025C_1v80 | max_fanout_violations | 1 | 1 |
| nom_tt_025C_1v80 | unannotated_routed_nets | 0 | 0 |
| nom_tt_025C_1v80 | fmax_estimate_mhz | 240.97 | 322.22 |
| nom_tt_025C_1v80 | constraint_warnings | 0 | 0 |
| nom_tt_025C_1v80 | unconstrained_endpoints | 0 | 0 |
| nom_ss_100C_1v60 | setup_ws_ns | 57.994549 | 2.326305 |
| nom_ss_100C_1v60 | hold_ws_ns | 0.953543 | 0.946097 |
| nom_ss_100C_1v60 | setup_wns_ns | 0 | 0 |
| nom_ss_100C_1v60 | hold_wns_ns | 0 | 0 |
| nom_ss_100C_1v60 | setup_tns_ns | 0 | 0 |
| nom_ss_100C_1v60 | hold_tns_ns | 0 | 0 |
| nom_ss_100C_1v60 | setup_violations | 0 | 0 |
| nom_ss_100C_1v60 | hold_violations | 0 | 0 |
| nom_ss_100C_1v60 | max_slew_violations | 0 | 0 |
| nom_ss_100C_1v60 | max_cap_violations | 0 | 0 |
| nom_ss_100C_1v60 | max_fanout_violations | 1 | 1 |
| nom_ss_100C_1v60 | unannotated_routed_nets | 0 | 0 |
| nom_ss_100C_1v60 | fmax_estimate_mhz | 125.64 | 173.47 |
| nom_ss_100C_1v60 | constraint_warnings | 0 | 0 |
| nom_ss_100C_1v60 | unconstrained_endpoints | 0 | 0 |
| nom_ff_n40C_1v95 | setup_ws_ns | 59.115694 | 5.292224 |
| nom_ff_n40C_1v95 | hold_ws_ns | 0.109737 | 0.112667 |
| nom_ff_n40C_1v95 | setup_wns_ns | 0 | 0 |
| nom_ff_n40C_1v95 | hold_wns_ns | 0 | 0 |
| nom_ff_n40C_1v95 | setup_tns_ns | 0 | 0 |
| nom_ff_n40C_1v95 | hold_tns_ns | 0 | 0 |
| nom_ff_n40C_1v95 | setup_violations | 0 | 0 |
| nom_ff_n40C_1v95 | hold_violations | 0 | 0 |
| nom_ff_n40C_1v95 | max_slew_violations | 0 | 0 |
| nom_ff_n40C_1v95 | max_cap_violations | 0 | 0 |
| nom_ff_n40C_1v95 | max_fanout_violations | 1 | 1 |
| nom_ff_n40C_1v95 | unannotated_routed_nets | 0 | 0 |
| nom_ff_n40C_1v95 | fmax_estimate_mhz | 380.76 | 469.39 |
| nom_ff_n40C_1v95 | constraint_warnings | 0 | 0 |
| nom_ff_n40C_1v95 | unconstrained_endpoints | 0 | 0 |
| min_tt_025C_1v80 | setup_ws_ns | 58.816555 | 5.068772 |
| min_tt_025C_1v80 | hold_ws_ns | 0.350368 | 0.334616 |
| min_tt_025C_1v80 | setup_wns_ns | 0 | 0 |
| min_tt_025C_1v80 | hold_wns_ns | 0 | 0 |
| min_tt_025C_1v80 | setup_tns_ns | 0 | 0 |
| min_tt_025C_1v80 | hold_tns_ns | 0 | 0 |
| min_tt_025C_1v80 | setup_violations | 0 | 0 |
| min_tt_025C_1v80 | hold_violations | 0 | 0 |
| min_tt_025C_1v80 | max_slew_violations | 0 | 0 |
| min_tt_025C_1v80 | max_cap_violations | 0 | 0 |
| min_tt_025C_1v80 | max_fanout_violations | 1 | 1 |
| min_tt_025C_1v80 | unannotated_routed_nets | 0 | 0 |
| min_tt_025C_1v80 | fmax_estimate_mhz | 243.17 | 329.75 |
| min_tt_025C_1v80 | constraint_warnings | 0 | 0 |
| min_tt_025C_1v80 | unconstrained_endpoints | 0 | 0 |
| min_ss_100C_1v60 | setup_ws_ns | 58.026396 | 2.390373 |
| min_ss_100C_1v60 | hold_ws_ns | 0.947701 | 0.93959 |
| min_ss_100C_1v60 | setup_wns_ns | 0 | 0 |
| min_ss_100C_1v60 | hold_wns_ns | 0 | 0 |
| min_ss_100C_1v60 | setup_tns_ns | 0 | 0 |
| min_ss_100C_1v60 | hold_tns_ns | 0 | 0 |
| min_ss_100C_1v60 | setup_violations | 0 | 0 |
| min_ss_100C_1v60 | hold_violations | 0 | 0 |
| min_ss_100C_1v60 | max_slew_violations | 0 | 0 |
| min_ss_100C_1v60 | max_cap_violations | 0 | 0 |
| min_ss_100C_1v60 | max_fanout_violations | 1 | 1 |
| min_ss_100C_1v60 | unannotated_routed_nets | 0 | 0 |
| min_ss_100C_1v60 | fmax_estimate_mhz | 126.71 | 175.08 |
| min_ss_100C_1v60 | constraint_warnings | 0 | 0 |
| min_ss_100C_1v60 | unconstrained_endpoints | 0 | 0 |
| min_ff_n40C_1v95 | setup_ws_ns | 59.127648 | 5.297113 |
| min_ff_n40C_1v95 | hold_ws_ns | 0.108355 | 0.110247 |
| min_ff_n40C_1v95 | setup_wns_ns | 0 | 0 |
| min_ff_n40C_1v95 | hold_wns_ns | 0 | 0 |
| min_ff_n40C_1v95 | setup_tns_ns | 0 | 0 |
| min_ff_n40C_1v95 | hold_tns_ns | 0 | 0 |
| min_ff_n40C_1v95 | setup_violations | 0 | 0 |
| min_ff_n40C_1v95 | hold_violations | 0 | 0 |
| min_ff_n40C_1v95 | max_slew_violations | 0 | 0 |
| min_ff_n40C_1v95 | max_cap_violations | 0 | 0 |
| min_ff_n40C_1v95 | max_fanout_violations | 1 | 1 |
| min_ff_n40C_1v95 | unannotated_routed_nets | 0 | 0 |
| min_ff_n40C_1v95 | fmax_estimate_mhz | 386.77 | 479.91 |
| min_ff_n40C_1v95 | constraint_warnings | 0 | 0 |
| min_ff_n40C_1v95 | unconstrained_endpoints | 0 | 0 |
| max_tt_025C_1v80 | setup_ws_ns | 58.779415 | 5.052206 |
| max_tt_025C_1v80 | hold_ws_ns | 0.357333 | 0.341338 |
| max_tt_025C_1v80 | setup_wns_ns | 0 | 0 |
| max_tt_025C_1v80 | hold_wns_ns | 0 | 0 |
| max_tt_025C_1v80 | setup_tns_ns | 0 | 0 |
| max_tt_025C_1v80 | hold_tns_ns | 0 | 0 |
| max_tt_025C_1v80 | setup_violations | 0 | 0 |
| max_tt_025C_1v80 | hold_violations | 0 | 0 |
| max_tt_025C_1v80 | max_slew_violations | 0 | 0 |
| max_tt_025C_1v80 | max_cap_violations | 0 | 0 |
| max_tt_025C_1v80 | max_fanout_violations | 1 | 1 |
| max_tt_025C_1v80 | unannotated_routed_nets | 0 | 0 |
| max_tt_025C_1v80 | fmax_estimate_mhz | 238.74 | 315.54 |
| max_tt_025C_1v80 | constraint_warnings | 0 | 0 |
| max_tt_025C_1v80 | unconstrained_endpoints | 0 | 0 |
| max_ss_100C_1v60 | setup_ws_ns | 57.963477 | 2.266873 |
| max_ss_100C_1v60 | hold_ws_ns | 0.956942 | 0.953093 |
| max_ss_100C_1v60 | setup_wns_ns | 0 | 0 |
| max_ss_100C_1v60 | hold_wns_ns | 0 | 0 |
| max_ss_100C_1v60 | setup_tns_ns | 0 | 0 |
| max_ss_100C_1v60 | hold_tns_ns | 0 | 0 |
| max_ss_100C_1v60 | setup_violations | 0 | 0 |
| max_ss_100C_1v60 | hold_violations | 0 | 0 |
| max_ss_100C_1v60 | max_slew_violations | 0 | 0 |
| max_ss_100C_1v60 | max_cap_violations | 0 | 0 |
| max_ss_100C_1v60 | max_fanout_violations | 1 | 1 |
| max_ss_100C_1v60 | unannotated_routed_nets | 0 | 0 |
| max_ss_100C_1v60 | fmax_estimate_mhz | 124.54 | 170.24 |
| max_ss_100C_1v60 | constraint_warnings | 0 | 0 |
| max_ss_100C_1v60 | unconstrained_endpoints | 0 | 0 |
| max_ff_n40C_1v95 | setup_ws_ns | 59.103913 | 5.286174 |
| max_ff_n40C_1v95 | hold_ws_ns | 0.111416 | 0.114879 |
| max_ff_n40C_1v95 | setup_wns_ns | 0 | 0 |
| max_ff_n40C_1v95 | hold_wns_ns | 0 | 0 |
| max_ff_n40C_1v95 | setup_tns_ns | 0 | 0 |
| max_ff_n40C_1v95 | hold_tns_ns | 0 | 0 |
| max_ff_n40C_1v95 | setup_violations | 0 | 0 |
| max_ff_n40C_1v95 | hold_violations | 0 | 0 |
| max_ff_n40C_1v95 | max_slew_violations | 0 | 0 |
| max_ff_n40C_1v95 | max_cap_violations | 0 | 0 |
| max_ff_n40C_1v95 | max_fanout_violations | 1 | 1 |
| max_ff_n40C_1v95 | unannotated_routed_nets | 0 | 0 |
| max_ff_n40C_1v95 | fmax_estimate_mhz | 375 | 460.22 |
| max_ff_n40C_1v95 | constraint_warnings | 0 | 0 |
| max_ff_n40C_1v95 | unconstrained_endpoints | 0 | 0 |

Escenarios discretos de proceso/interconexión: **B02 azul**, **B04 naranja**. Las líneas no interpolan corners físicos nuevos.

```mermaid
---
config:
  themeVariables:
    xyChart:
      plotColorPalette: '#2563eb, #ea580c'
---
xychart-beta
    title "setup_ws_ns: target"
    x-axis ["nom-TT", "nom-SS", "nom-FF", "min-TT", "min-SS", "min-FF", "max-TT", "max-SS", "max-FF"]
    y-axis "ns" 0.000000000000 --> 62.084030873527
    line [58.797697264155, 57.994549470929, 59.115693569111, 58.816555068895, 58.026395997246, 59.127648450978, 58.779414999047, 57.963477436215, 59.103912770219]
    line [5.061287532339, 2.326305436352, 5.292224142045, 5.068772212094, 2.390373300290, 5.297113120294, 5.052205907741, 2.266872975716, 5.286173870478]
```

[Fuente Mermaid](time_comparison/target-setup_ws_ns.mmd)

```mermaid
---
config:
  themeVariables:
    xyChart:
      plotColorPalette: '#2563eb, #ea580c'
---
xychart-beta
    title "hold_ws_ns: target"
    x-axis ["nom-TT", "nom-SS", "nom-FF", "min-TT", "min-SS", "min-FF", "max-TT", "max-SS", "max-FF"]
    y-axis "ns" 0.000000000000 --> 1.004789446753
    line [0.354653538797, 0.953543049288, 0.109737499971, 0.350368466379, 0.947700833522, 0.108355216755, 0.357332562542, 0.956942330241, 0.111415824165]
    line [0.338198645328, 0.946097338362, 0.112667267593, 0.334616066549, 0.939589987964, 0.110247425420, 0.341338356130, 0.953092520771, 0.114878831921]
```

[Fuente Mermaid](time_comparison/target-hold_ws_ns.mmd)

```mermaid
---
config:
  themeVariables:
    xyChart:
      plotColorPalette: '#2563eb, #ea580c'
---
xychart-beta
    title "setup_tns_ns: target"
    x-axis ["nom-TT", "nom-SS", "nom-FF", "min-TT", "min-SS", "min-FF", "max-TT", "max-SS", "max-FF"]
    y-axis "ns" 0.000000000000 --> 1.000000000000
    line [0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000]
    line [0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000]
```

[Fuente Mermaid](time_comparison/target-setup_tns_ns.mmd)

```mermaid
---
config:
  themeVariables:
    xyChart:
      plotColorPalette: '#2563eb, #ea580c'
---
xychart-beta
    title "hold_tns_ns: target"
    x-axis ["nom-TT", "nom-SS", "nom-FF", "min-TT", "min-SS", "min-FF", "max-TT", "max-SS", "max-FF"]
    y-axis "ns" 0.000000000000 --> 1.000000000000
    line [0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000]
    line [0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000]
```

[Fuente Mermaid](time_comparison/target-hold_tns_ns.mmd)

```mermaid
---
config:
  themeVariables:
    xyChart:
      plotColorPalette: '#2563eb, #ea580c'
---
xychart-beta
    title "fmax_estimate_mhz: target"
    x-axis ["nom-TT", "nom-SS", "nom-FF", "min-TT", "min-SS", "min-FF", "max-TT", "max-SS", "max-FF"]
    y-axis "MHz" 0.000000000000 --> 503.905500000000
    line [240.970000000000, 125.640000000000, 380.760000000000, 243.170000000000, 126.710000000000, 386.770000000000, 238.740000000000, 124.540000000000, 375.000000000000]
    line [322.220000000000, 173.470000000000, 469.390000000000, 329.750000000000, 175.080000000000, 479.910000000000, 315.540000000000, 170.240000000000, 460.220000000000]
```

[Fuente Mermaid](time_comparison/target-fmax_estimate_mhz.mmd)

Escenario common: B02 setup/hold **PASS**, eléctrico/restricciones **FAIL**, global **FAIL**; B04 setup/hold **PASS**, eléctrico/restricciones **FAIL**, global **FAIL**.

| Estado | B02 | B04 |
|---|---|---|
| Setup/hold | PASS | PASS |
| Eléctrico/restricciones | FAIL | FAIL |
| Global | FAIL | FAIL |

| Corner | Métrica | B02 | B04 |
|---|---|---:|---:|
| nom_tt_025C_1v80 | setup_ws_ns | 58.797697 | 59.061287 |
| nom_tt_025C_1v80 | hold_ws_ns | 0.354654 | 0.338199 |
| nom_tt_025C_1v80 | setup_wns_ns | 0 | 0 |
| nom_tt_025C_1v80 | hold_wns_ns | 0 | 0 |
| nom_tt_025C_1v80 | setup_tns_ns | 0 | 0 |
| nom_tt_025C_1v80 | hold_tns_ns | 0 | 0 |
| nom_tt_025C_1v80 | setup_violations | 0 | 0 |
| nom_tt_025C_1v80 | hold_violations | 0 | 0 |
| nom_tt_025C_1v80 | max_slew_violations | 0 | 0 |
| nom_tt_025C_1v80 | max_cap_violations | 0 | 0 |
| nom_tt_025C_1v80 | max_fanout_violations | 1 | 1 |
| nom_tt_025C_1v80 | unannotated_routed_nets | 0 | 0 |
| nom_tt_025C_1v80 | fmax_estimate_mhz | 240.97 | 322.22 |
| nom_tt_025C_1v80 | constraint_warnings | 0 | 0 |
| nom_tt_025C_1v80 | unconstrained_endpoints | 0 | 0 |
| nom_ss_100C_1v60 | setup_ws_ns | 57.994549 | 58.458491 |
| nom_ss_100C_1v60 | hold_ws_ns | 0.953543 | 0.946097 |
| nom_ss_100C_1v60 | setup_wns_ns | 0 | 0 |
| nom_ss_100C_1v60 | hold_wns_ns | 0 | 0 |
| nom_ss_100C_1v60 | setup_tns_ns | 0 | 0 |
| nom_ss_100C_1v60 | hold_tns_ns | 0 | 0 |
| nom_ss_100C_1v60 | setup_violations | 0 | 0 |
| nom_ss_100C_1v60 | hold_violations | 0 | 0 |
| nom_ss_100C_1v60 | max_slew_violations | 0 | 0 |
| nom_ss_100C_1v60 | max_cap_violations | 0 | 0 |
| nom_ss_100C_1v60 | max_fanout_violations | 1 | 1 |
| nom_ss_100C_1v60 | unannotated_routed_nets | 0 | 0 |
| nom_ss_100C_1v60 | fmax_estimate_mhz | 125.64 | 173.47 |
| nom_ss_100C_1v60 | constraint_warnings | 0 | 0 |
| nom_ss_100C_1v60 | unconstrained_endpoints | 0 | 0 |
| nom_ff_n40C_1v95 | setup_ws_ns | 59.115694 | 59.292221 |
| nom_ff_n40C_1v95 | hold_ws_ns | 0.109737 | 0.112667 |
| nom_ff_n40C_1v95 | setup_wns_ns | 0 | 0 |
| nom_ff_n40C_1v95 | hold_wns_ns | 0 | 0 |
| nom_ff_n40C_1v95 | setup_tns_ns | 0 | 0 |
| nom_ff_n40C_1v95 | hold_tns_ns | 0 | 0 |
| nom_ff_n40C_1v95 | setup_violations | 0 | 0 |
| nom_ff_n40C_1v95 | hold_violations | 0 | 0 |
| nom_ff_n40C_1v95 | max_slew_violations | 0 | 0 |
| nom_ff_n40C_1v95 | max_cap_violations | 0 | 0 |
| nom_ff_n40C_1v95 | max_fanout_violations | 1 | 1 |
| nom_ff_n40C_1v95 | unannotated_routed_nets | 0 | 0 |
| nom_ff_n40C_1v95 | fmax_estimate_mhz | 380.76 | 469.39 |
| nom_ff_n40C_1v95 | constraint_warnings | 0 | 0 |
| nom_ff_n40C_1v95 | unconstrained_endpoints | 0 | 0 |
| min_tt_025C_1v80 | setup_ws_ns | 58.816555 | 59.068769 |
| min_tt_025C_1v80 | hold_ws_ns | 0.350368 | 0.334616 |
| min_tt_025C_1v80 | setup_wns_ns | 0 | 0 |
| min_tt_025C_1v80 | hold_wns_ns | 0 | 0 |
| min_tt_025C_1v80 | setup_tns_ns | 0 | 0 |
| min_tt_025C_1v80 | hold_tns_ns | 0 | 0 |
| min_tt_025C_1v80 | setup_violations | 0 | 0 |
| min_tt_025C_1v80 | hold_violations | 0 | 0 |
| min_tt_025C_1v80 | max_slew_violations | 0 | 0 |
| min_tt_025C_1v80 | max_cap_violations | 0 | 0 |
| min_tt_025C_1v80 | max_fanout_violations | 1 | 1 |
| min_tt_025C_1v80 | unannotated_routed_nets | 0 | 0 |
| min_tt_025C_1v80 | fmax_estimate_mhz | 243.17 | 329.75 |
| min_tt_025C_1v80 | constraint_warnings | 0 | 0 |
| min_tt_025C_1v80 | unconstrained_endpoints | 0 | 0 |
| min_ss_100C_1v60 | setup_ws_ns | 58.026396 | 58.468517 |
| min_ss_100C_1v60 | hold_ws_ns | 0.947701 | 0.93959 |
| min_ss_100C_1v60 | setup_wns_ns | 0 | 0 |
| min_ss_100C_1v60 | hold_wns_ns | 0 | 0 |
| min_ss_100C_1v60 | setup_tns_ns | 0 | 0 |
| min_ss_100C_1v60 | hold_tns_ns | 0 | 0 |
| min_ss_100C_1v60 | setup_violations | 0 | 0 |
| min_ss_100C_1v60 | hold_violations | 0 | 0 |
| min_ss_100C_1v60 | max_slew_violations | 0 | 0 |
| min_ss_100C_1v60 | max_cap_violations | 0 | 0 |
| min_ss_100C_1v60 | max_fanout_violations | 1 | 1 |
| min_ss_100C_1v60 | unannotated_routed_nets | 0 | 0 |
| min_ss_100C_1v60 | fmax_estimate_mhz | 126.71 | 175.08 |
| min_ss_100C_1v60 | constraint_warnings | 0 | 0 |
| min_ss_100C_1v60 | unconstrained_endpoints | 0 | 0 |
| min_ff_n40C_1v95 | setup_ws_ns | 59.127648 | 59.297109 |
| min_ff_n40C_1v95 | hold_ws_ns | 0.108355 | 0.110247 |
| min_ff_n40C_1v95 | setup_wns_ns | 0 | 0 |
| min_ff_n40C_1v95 | hold_wns_ns | 0 | 0 |
| min_ff_n40C_1v95 | setup_tns_ns | 0 | 0 |
| min_ff_n40C_1v95 | hold_tns_ns | 0 | 0 |
| min_ff_n40C_1v95 | setup_violations | 0 | 0 |
| min_ff_n40C_1v95 | hold_violations | 0 | 0 |
| min_ff_n40C_1v95 | max_slew_violations | 0 | 0 |
| min_ff_n40C_1v95 | max_cap_violations | 0 | 0 |
| min_ff_n40C_1v95 | max_fanout_violations | 1 | 1 |
| min_ff_n40C_1v95 | unannotated_routed_nets | 0 | 0 |
| min_ff_n40C_1v95 | fmax_estimate_mhz | 386.77 | 479.91 |
| min_ff_n40C_1v95 | constraint_warnings | 0 | 0 |
| min_ff_n40C_1v95 | unconstrained_endpoints | 0 | 0 |
| max_tt_025C_1v80 | setup_ws_ns | 58.779415 | 59.052203 |
| max_tt_025C_1v80 | hold_ws_ns | 0.357333 | 0.341338 |
| max_tt_025C_1v80 | setup_wns_ns | 0 | 0 |
| max_tt_025C_1v80 | hold_wns_ns | 0 | 0 |
| max_tt_025C_1v80 | setup_tns_ns | 0 | 0 |
| max_tt_025C_1v80 | hold_tns_ns | 0 | 0 |
| max_tt_025C_1v80 | setup_violations | 0 | 0 |
| max_tt_025C_1v80 | hold_violations | 0 | 0 |
| max_tt_025C_1v80 | max_slew_violations | 0 | 0 |
| max_tt_025C_1v80 | max_cap_violations | 0 | 0 |
| max_tt_025C_1v80 | max_fanout_violations | 1 | 1 |
| max_tt_025C_1v80 | unannotated_routed_nets | 0 | 0 |
| max_tt_025C_1v80 | fmax_estimate_mhz | 238.74 | 315.54 |
| max_tt_025C_1v80 | constraint_warnings | 0 | 0 |
| max_tt_025C_1v80 | unconstrained_endpoints | 0 | 0 |
| max_ss_100C_1v60 | setup_ws_ns | 57.963477 | 58.442596 |
| max_ss_100C_1v60 | hold_ws_ns | 0.956942 | 0.953093 |
| max_ss_100C_1v60 | setup_wns_ns | 0 | 0 |
| max_ss_100C_1v60 | hold_wns_ns | 0 | 0 |
| max_ss_100C_1v60 | setup_tns_ns | 0 | 0 |
| max_ss_100C_1v60 | hold_tns_ns | 0 | 0 |
| max_ss_100C_1v60 | setup_violations | 0 | 0 |
| max_ss_100C_1v60 | hold_violations | 0 | 0 |
| max_ss_100C_1v60 | max_slew_violations | 0 | 0 |
| max_ss_100C_1v60 | max_cap_violations | 0 | 0 |
| max_ss_100C_1v60 | max_fanout_violations | 1 | 1 |
| max_ss_100C_1v60 | unannotated_routed_nets | 0 | 0 |
| max_ss_100C_1v60 | fmax_estimate_mhz | 124.54 | 170.24 |
| max_ss_100C_1v60 | constraint_warnings | 0 | 0 |
| max_ss_100C_1v60 | unconstrained_endpoints | 0 | 0 |
| max_ff_n40C_1v95 | setup_ws_ns | 59.103913 | 59.286171 |
| max_ff_n40C_1v95 | hold_ws_ns | 0.111416 | 0.114879 |
| max_ff_n40C_1v95 | setup_wns_ns | 0 | 0 |
| max_ff_n40C_1v95 | hold_wns_ns | 0 | 0 |
| max_ff_n40C_1v95 | setup_tns_ns | 0 | 0 |
| max_ff_n40C_1v95 | hold_tns_ns | 0 | 0 |
| max_ff_n40C_1v95 | setup_violations | 0 | 0 |
| max_ff_n40C_1v95 | hold_violations | 0 | 0 |
| max_ff_n40C_1v95 | max_slew_violations | 0 | 0 |
| max_ff_n40C_1v95 | max_cap_violations | 0 | 0 |
| max_ff_n40C_1v95 | max_fanout_violations | 1 | 1 |
| max_ff_n40C_1v95 | unannotated_routed_nets | 0 | 0 |
| max_ff_n40C_1v95 | fmax_estimate_mhz | 375 | 460.22 |
| max_ff_n40C_1v95 | constraint_warnings | 0 | 0 |
| max_ff_n40C_1v95 | unconstrained_endpoints | 0 | 0 |

Escenarios discretos de proceso/interconexión: **B02 azul**, **B04 naranja**. Las líneas no interpolan corners físicos nuevos.

```mermaid
---
config:
  themeVariables:
    xyChart:
      plotColorPalette: '#2563eb, #ea580c'
---
xychart-beta
    title "setup_ws_ns: common"
    x-axis ["nom-TT", "nom-SS", "nom-FF", "min-TT", "min-SS", "min-FF", "max-TT", "max-SS", "max-FF"]
    y-axis "ns" 0.000000000000 --> 62.261964812813
    line [58.797697264155, 57.994549470929, 59.115693569111, 58.816555068895, 58.026395997246, 59.127648450978, 58.779414999047, 57.963477436215, 59.103912770219]
    line [59.061287310295, 58.458491257937, 59.292220811375, 59.068769325514, 58.468517016222, 59.297109345536, 59.052203021161, 58.442596416489, 59.286170539809]
```

[Fuente Mermaid](time_comparison/common-setup_ws_ns.mmd)

```mermaid
---
config:
  themeVariables:
    xyChart:
      plotColorPalette: '#2563eb, #ea580c'
---
xychart-beta
    title "hold_ws_ns: common"
    x-axis ["nom-TT", "nom-SS", "nom-FF", "min-TT", "min-SS", "min-FF", "max-TT", "max-SS", "max-FF"]
    y-axis "ns" 0.000000000000 --> 1.004789446753
    line [0.354653538797, 0.953543049288, 0.109737499971, 0.350368466379, 0.947700833522, 0.108355216755, 0.357332562542, 0.956942330241, 0.111415824165]
    line [0.338198645328, 0.946097338362, 0.112667267593, 0.334616066549, 0.939589987964, 0.110247425420, 0.341338356130, 0.953092520771, 0.114878831921]
```

[Fuente Mermaid](time_comparison/common-hold_ws_ns.mmd)

```mermaid
---
config:
  themeVariables:
    xyChart:
      plotColorPalette: '#2563eb, #ea580c'
---
xychart-beta
    title "setup_tns_ns: common"
    x-axis ["nom-TT", "nom-SS", "nom-FF", "min-TT", "min-SS", "min-FF", "max-TT", "max-SS", "max-FF"]
    y-axis "ns" 0.000000000000 --> 1.000000000000
    line [0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000]
    line [0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000]
```

[Fuente Mermaid](time_comparison/common-setup_tns_ns.mmd)

```mermaid
---
config:
  themeVariables:
    xyChart:
      plotColorPalette: '#2563eb, #ea580c'
---
xychart-beta
    title "hold_tns_ns: common"
    x-axis ["nom-TT", "nom-SS", "nom-FF", "min-TT", "min-SS", "min-FF", "max-TT", "max-SS", "max-FF"]
    y-axis "ns" 0.000000000000 --> 1.000000000000
    line [0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000]
    line [0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000, 0.000000000000]
```

[Fuente Mermaid](time_comparison/common-hold_tns_ns.mmd)

```mermaid
---
config:
  themeVariables:
    xyChart:
      plotColorPalette: '#2563eb, #ea580c'
---
xychart-beta
    title "fmax_estimate_mhz: common"
    x-axis ["nom-TT", "nom-SS", "nom-FF", "min-TT", "min-SS", "min-FF", "max-TT", "max-SS", "max-FF"]
    y-axis "MHz" 0.000000000000 --> 503.905500000000
    line [240.970000000000, 125.640000000000, 380.760000000000, 243.170000000000, 126.710000000000, 386.770000000000, 238.740000000000, 124.540000000000, 375.000000000000]
    line [322.220000000000, 173.470000000000, 469.390000000000, 329.750000000000, 175.080000000000, 479.910000000000, 315.540000000000, 170.240000000000, 460.220000000000]
```

[Fuente Mermaid](time_comparison/common-fmax_estimate_mhz.mmd)

<!-- comparison:end -->
