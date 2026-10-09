# Contrato: verificación, SQNR y PPA

**Estado:** Abierto
**Prepara:** @andres332271
**Revisan:** @moreyrajulian y @EnzoFernandezz11
**Issues:** E03, A04–A07, I01

## Vector matching

| Aspecto | Decisión |
|---|---|
| Modelo de referencia de cada variante | Por definir. |
| Casos mínimos | Impulso, ceros, QPSK determinista, extremos y límites de bloque. |
| Semilla y número de vectores smoke/regresión | Por definir. |
| Comparación exacta o tolerancia por variante | Por definir. |
| Alineación por índice y descarte de transitorios | Por índice de resultado aceptado, no por ciclo ([interfaz](interfaz-rtl.md#latencia-y-throughput), E03). Descarte de transitorios: por definir con D07. |
| Mensaje de falla | Variante, índice, I/Q esperado/obtenido, formato y semilla. |

Cada testbench compara por **índice de muestra válido** con su modelo fijo. Las diferencias entre dominios pueden necesitar tolerancia numérica por distintos puntos de redondeo: registrar la tolerancia, no ocultar discrepancias.

## SQNR

El mínimo exigido es **SQNR ≥ 40 dB**, confirmado por Enzo el 7/10/2026 como aclaración adicional a la consigna vigente. Antes de reportarla, fijar si la referencia es la salida flotante del filtro temporal o una referencia por dominio, la escala aplicada, el tramo de muestras y el tratamiento de I/Q. Una fórmula candidata para revisar es `10·log10(Σ|y_ref|² / Σ|y_fxp−y_ref|²)` sobre muestras válidas alineadas. No registrar un número aislado sin su configuración y vectores.

## PPA

**Propuesta E03 (D05, D06):** todas las variantes se miden con **Vivado** sobre la misma FPGA Xilinx, con el mismo flujo y las mismas constraints. La CI no tiene Vivado: el `full` de Yosys sigue sirviendo para comprobar que el RTL es sintetizable, pero las cifras PPA salen de las corridas Vivado registradas en `reports/`.

| Condición común | Valor propuesto |
|---|---|
| Herramienta | Vivado, versión anotada en cada reporte. |
| Dispositivo | Artix-7 `xc7a35tcpg236-1` (placa Basys3). |
| Flujo | Síntesis e implementación (place & route) **out-of-context** del núcleo: sin pines de E/S ni drivers del testbench, para medir solo el filtro. Estrategias por defecto. |
| Constraints | Solo el reloj: `constraints/clk_100mhz.xdc` (período 10 ns) para variantes rápidas y `constraints/clk_10mhz.xdc` (100 ns) para lentas. |
| Corner y temperatura | Los que Vivado usa por defecto para el dispositivo (grado de velocidad −1, condiciones típicas de `report_power`). |

| Métrica | Definición y herramienta |
|---|---|
| Área | `report_utilization` después de implementar: LUT, FF, DSP48 y BRAM. Se reportan las cuatro cifras, sin convertirlas a un único número. |
| Performance | `report_timing_summary` después de implementar, al reloj objetivo de la variante: debe cumplir WNS ≥ 0. Fmax = 1 / (T − WNS). Latencia `L`, `II` y throughput `f_clk / II` según el [contrato de interfaz](interfaz-rtl.md#latencia-y-throughput), medidos en simulación. |
| Potencia | `report_power` después de implementar, con actividad **SAIF** de una simulación del diseño implementado en xsim con el mismo vector QPSK (semilla y longitud de A05), al reloj objetivo de la variante. Se reportan la potencia dinámica y la estática por separado, y la **energía por muestra** = P_dinámica / throughput, que permite comparar variantes con relojes distintos. |

El reloj mínimo es 100 MHz para variantes rápidas y 10 MHz para lentas, confirmado por Enzo el 7/10/2026; verificar timing a la frecuencia de operación elegida. Una estimación sin SAIF (actividad por defecto o *vectorless*) se puede anotar como referencia, pero no es potencia comparable.

La tabla final tendrá columnas `variante`, `commit`, `configuración`, `SQNR`, `área`, `Fmax`, `latencia`, `throughput`, `potencia`, `herramienta/log`. Si una métrica no se puede medir con las herramientas disponibles, dejarla como «no medida» y explicar la limitación. No presentar el mapeo lógico de Yosys como Fmax medido ni una estimación sin actividad como potencia comparable.

## Condiciones para aprobar

- [ ] @moreyrajulian y @EnzoFernandezz11 pueden ejecutar los mismos vectores y saber qué salida se compara.
- [ ] El método de SQNR reproduce el mismo resultado desde la configuración y los datos.
- [ ] Las cuatro variantes usarán tecnología y constraints comunes para área/timing.
- [ ] La metodología de potencia identifica su herramienta y fuente de actividad.
