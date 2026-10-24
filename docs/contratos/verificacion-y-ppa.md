# Contrato: verificación, SQNR y PPA

**Estado:** Abierto
**Prepara:** @andres332271
**Revisan:** @moreyrajulian y @EnzoFernandezz11
**Issues:** E03, A04–A07, I01

## Vector matching

| Aspecto | Decisión |
|---|---|
| Modelo de referencia de cada variante | Modelo fijo de su rama (A04): `fir_time_fxp` para B, `fir_frequency_fxp` para C. Columnas `yt` y `yf` de [vectors/](../../vectors/README.md). |
| Casos mínimos | Impulso, ceros, QPSK determinista, extremos y límites de bloque. |
| Semilla y número de vectores smoke/regresión | Smoke: impulso, ceros, extremos y bordes (426 muestras). Regresión: además `build/vectors/qpsk_s1.txt`, semilla 1 y 1024 símbolos, generado con el mismo comando. Ver [vectors/](../../vectors/README.md). |
| Comparación exacta o tolerancia por variante | Exacta contra el modelo fijo de su rama. Entre ramas, ≤ 2 LSB (A04). |
| Alineación por índice y descarte de transitorios | Por índice de resultado aceptado, no por ciclo ([interfaz](interfaz-rtl.md#latencia-y-throughput), E03). Descarte de transitorios: por definir con D07. |
| Mensaje de falla | Variante, índice, I/Q esperado/obtenido, formato y semilla. |

Cada testbench compara por **índice de muestra válido** con su modelo fijo. Las diferencias entre dominios pueden necesitar tolerancia numérica por distintos puntos de redondeo: registrar la tolerancia, no ocultar discrepancias.

## SQNR

El mínimo exigido es **SQNR ≥ 40 dB**, confirmado por Enzo el 7/10/2026 como aclaración adicional a la consigna vigente. No registrar un número aislado sin su configuración y vectores.

**Definición propuesta (D07, A04):**

| Aspecto | Propuesta |
|---|---|
| Referencia | Una sola para ambas ramas: el FIR temporal flotante `fir_time(x, h)` con los coeficientes de E02 sin cuantizar. Las dos ramas implementan el mismo filtro, así que la referencia mide también el error de cuantizar h, H y W. |
| Fórmula | `SQNR = 10·log10(Σ|y_ref|² / Σ|y_fxp − y_ref|²)`, con `y_fxp` = salida entera / 2^7. I e Q juntas como valor complejo. |
| Muestras | Todas, alineadas por índice. Sin descarte: ambas ramas arrancan con historial cero, igual que la referencia. |
| Casos | QPSK 2× con semillas 0–4 y 1024 símbolos cada una (2048 muestras); se reporta la **mínima** entre semillas. |
| Comando | `python3 -m model.fixed_point`; `tests/test_fixed_point.py` lo comprueba en `make smoke`. |

**Tolerancia entre ramas en punto fijo:** cada RTL coincide **palabra por palabra** con su modelo fijo. Entre ramas, las salidas fijas temporal y de frecuencia difieren como máximo en **2 LSB** por componente (máximo observado con los casos de arriba), porque redondean en lugares distintos.

## PPA

**Extensión física aprobada por Enzo (24/10/2026, C02/C04):** usar OpenLane 2
local fijado mediante Nix y SKY130 HD. La metodología sigue el material del
curso: síntesis → implementación física → SPEF → STA en nueve corners y potencia
con actividad completa del benchmark sobre la netlist final. Setup/hold mediante
STA post-ruteo sustituye la exigencia de simulación SDF para este análisis; SDF
queda como verificación adicional. Vivado continúa como referencia FPGA.
Los objetivos mínimos no cambian; un resultado timing FAIL se declara, no se
reclasifica la variante ni se modifica su arquitectura automáticamente.
La potencia funcional sin retardos es una estimación y la cobertura del origen
de actividad por pin se registra. La comparación común usa 10 MHz sólo cuando ambas variantes
cumplen STA. Ver [procedimiento físico y Mermaid](../frecuencia/ppa.md).
La adopción del método no implica que las mediciones físicas ya estén obtenidas.

**Actualización de Enzo del 22/10/2026 (C02 y C04):** la comparación local vigente
es ASIC **SKY130 HD de 130 nm**, con biblioteca `sky130_fd_sc_hd__tt_025C_1v80.lib`
(TT, 25 °C, 1,8 V). Yosys sintetiza y mapea ambas variantes con el mismo flujo;
se registran celdas, flip-flops, área de celdas en µm², versiones y SHA256 de la
biblioteca y fuentes. El área es una suma Liberty; no incluye floorplan, ruteo,
árbol de reloj ni macros SRAM. El flujo vigente no mide timing ni potencia ASIC.
La adopción y medición de este mismo flujo en las variantes temporales queda pendiente.

La simulación mantiene comparación exacta A04/A05 y mide latencia e intervalo.
Los mínimos objetivo siguen siendo 10 MHz para lentas y 100 MHz para rápidas;
el reloj configurado en el banco no demuestra que el circuito cierre timing.
Fmax/WNS/setup/hold requieren STA y restricciones declaradas. Para resultados
físicos hacen falta implementación y parasíticos. Potencia dinámica/estática y
energía por muestra requieren biblioteca, actividad y condiciones comparables;
se reportan como no medidas hasta disponer de esa evidencia.

Vivado/Artix-7 queda como referencia FPGA independiente. Se conserva el resumen
histórico C02 recibido de Windows y el generador de paquetes para futuras
comparaciones FPGA. Sus LUT, DSP, timing y potencia no se convierten a cifras ASIC.

**Mantenimiento de resultados:** `reports/ppa/frequency.md` muestra solamente la
última corrida exitosa de cada variante, reemplazando la anterior incluso cuando
es equivalente. Los artefactos anteriores quedan en `build/ppa/`; la referencia
histórica Vivado C02 se conserva fuera de las regiones reemplazables. No actualizar
resultados con una corrida fallida. Ver el [procedimiento](../frecuencia/ppa.md).

## Condiciones para aprobar

- [ ] @moreyrajulian y @EnzoFernandezz11 pueden ejecutar los mismos vectores y saber qué salida se compara.
- [ ] El método de SQNR reproduce el mismo resultado desde la configuración y los datos.
- [ ] Las cuatro variantes usarán tecnología y constraints comunes para área/timing.
- [ ] La metodología de potencia identifica su herramienta y fuente de actividad.
