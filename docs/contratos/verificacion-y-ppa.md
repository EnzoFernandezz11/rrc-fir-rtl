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

**Acuerdo del equipo (26/10/2026, D05/D06):** @EnzoFernandezz11,
@andres332271 y @moreyrajulian adoptan OpenLane 2 fijado mediante Nix y
**SKY130 HD de 130 nm** para B02, B04, C02 y C04. El flujo cubre síntesis,
floorplan, placement, CTS, ruteo, extracción SPEF y STA post-ruteo en las nueve
combinaciones TT/SS/FF × RC nom/min/max. El procedimiento y las versiones están
en la [guía PPA](../frecuencia/ppa.md). El área final de celdas, core y die se
informa por separado del área Liberty de síntesis.

Los objetivos son **10 MHz en seriales y 100 MHz en optimizadas**. Para informar
cumplimiento de setup/hold se exige slack no negativo y cero violaciones de ambos
chequeos en **los nueve corners**. La tabla muestra el peor slack de setup y el
peor slack de hold, cada uno con su corner; TT nominal puede mostrarse como dato
adicional. Fmax es una estimación registro a registro y no sustituye esta condición.
Las restricciones eléctricas (**slew, capacitancia y fanout**) tienen un veredicto
separado, incluidos los buffers insertados por CTS. **PASS global** requiere
setup/hold y eléctrico PASS, restricciones completas y parasíticos anotados.
Un FAIL se declara sin reclasificar la variante ni reducir su objetivo.

La netlist final se simula funcionalmente con comparación exacta A04/A05. El
período del banco no demuestra cierre temporal; setup/hold se evalúan mediante
STA con SPEF. La simulación SDF queda como comprobación adicional.

La potencia se estima con **OpenSTA**, Liberty TT/25 °C/1,8 V, **SPEF nominal**,
SDC declarado y **VCD de la netlist final**. Las cuatro variantes usan QPSK 2×,
semilla 1 y 2048 muestras. Se procesa la ventana activa completa en segmentos,
se pondera la potencia por duración y se calcula energía por muestra como
potencia × duración activa / 2048. Se informa interna, switching, dinámica,
leakage y total, junto con la cobertura de actividad por pin. La actividad
funcional sin retardos no captura todos los glitches temporales. Cada escenario
publica las restricciones usadas por STA y potencia, incluidas sus diferencias.

C02/C04 ya tienen corridas físicas en [el reporte de frecuencia](../../reports/ppa/frequency.md).
Julián informó las mediciones B02/B04 con el mismo flujo en su revisión de #56;
su integración y la tabla conjunta se completan con B04 y A07. Tener una corrida
completa no implica cierre: C04 pasa setup/hold en TT a 100 MHz, falla en SS y
mantiene violaciones eléctricas. Las comparaciones físicas a reloj común deben
explicitar ambos veredictos; los gráficos que presuponen cumplimiento quedan
condicionados a PASS global de las variantes comparadas.

**Referencia FPGA:** se conservan `scripts/ppa/vivado/` y los reportes de
`reports/ppa/time_serial/` y `reports/ppa/frequency_serial/`. La corrida C04 de
#57 se destina al anexo FPGA. Sus métricas Artix-7 no se convierten a área ni
potencia ASIC; la tabla principal A07 utilizará SKY130 para las cuatro variantes.

**Evidencia y mantenimiento:** se publica el subconjunto pequeño de la última
corrida completa en `reports/ppa/<target>/sky130/`: manifiesto, métricas JSON,
configuraciones OpenLane, SDC, logs de potencia y resúmenes STA por corner.
`evidence.json` identifica la corrida de origen y los SHA256 de los archivos.
Los VCD, netlists, SPEF, SDF, ODB y bibliotecas permanecen en `build/ppa/`.
Una corrida completa con timing FAIL se publica con ese resultado; una falla de
herramienta o evidencia incompleta no reemplaza la medición válida anterior.
Las referencias FPGA se conservan junto a la evidencia ASIC.

## Condiciones para aprobar

- [ ] @moreyrajulian y @EnzoFernandezz11 pueden ejecutar los mismos vectores y saber qué salida se compara.
- [ ] El método de SQNR reproduce el mismo resultado desde la configuración y los datos.
- [ ] Las cuatro variantes usarán tecnología y constraints comunes para área/timing.
- [ ] La metodología de potencia identifica su herramienta y fuente de actividad.
