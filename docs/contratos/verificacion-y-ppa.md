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
| Alineación por índice y descarte de transitorios | Por definir. |
| Mensaje de falla | Variante, índice, I/Q esperado/obtenido, formato y semilla. |

Cada testbench compara por **índice de muestra válido** con su modelo fijo. Las diferencias entre dominios pueden necesitar tolerancia numérica por distintos puntos de redondeo: registrar la tolerancia, no ocultar discrepancias.

## SQNR

El mínimo exigido es **SQNR ≥ 40 dB**, confirmado por Enzo el 7/10/2026 como aclaración adicional a la consigna vigente. Antes de reportarla, fijar si la referencia es la salida flotante del filtro temporal o una referencia por dominio, la escala aplicada, el tramo de muestras y el tratamiento de I/Q. Una fórmula candidata para revisar es `10·log10(Σ|y_ref|² / Σ|y_fxp−y_ref|²)` sobre muestras válidas alineadas. No registrar un número aislado sin su configuración y vectores.

## PPA

| Métrica | Definición y herramienta a acordar |
|---|---|
| Área | FPGA: LUT/FF/DSP; ASIC: área de celdas. Misma tecnología y constraints. |
| Performance | Fmax medido, latencia en ciclos y throughput en muestras/s. Reloj mínimo de 100 MHz en variantes rápidas y 10 MHz en lentas, confirmado por Enzo el 7/10/2026; verificar timing a la frecuencia de operación elegida. |
| Potencia | Herramienta, actividad de entrada, reloj, tecnología y corner pendientes. |

La tabla final tendrá columnas `variante`, `commit`, `configuración`, `SQNR`, `área`, `Fmax`, `latencia`, `throughput`, `potencia`, `herramienta/log`. Si una métrica no se puede medir con las herramientas disponibles, dejarla como «no medida» y explicar la limitación. No presentar el mapeo lógico de Yosys como Fmax medido ni una estimación sin actividad como potencia comparable.

## Condiciones para aprobar

- [ ] @moreyrajulian y @EnzoFernandezz11 pueden ejecutar los mismos vectores y saber qué salida se compara.
- [ ] El método de SQNR reproduce el mismo resultado desde la configuración y los datos.
- [ ] Las cuatro variantes usarán tecnología y constraints comunes para área/timing.
- [ ] La metodología de potencia identifica su herramienta y fuente de actividad.
