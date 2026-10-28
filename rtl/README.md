# RTL

Ubicar las variantes temporal serial/optimizada en `time/`, la frecuencia serial en `frequency/` y la optimizada en `frequency_optimized/`. `common/` recibe solo módulos compartidos de verdad. Cada variante integrada debe añadirse a [`config/rtl_targets.json`](../config/rtl_targets.json) junto con su testbench y, cuando exista, script de síntesis.

El formato de una entrada del registro es:

```json
{
  "name": "time_serial",
  "domain": "time",
  "architecture": "serial",
  "rtl_top": "fir_time_serial",
  "testbench_top": "tb_fir_time_serial",
  "sources": ["rtl/time/fir_time_serial.sv"],
  "testbench": "tb/time/tb_fir_time_serial.sv",
  "synth_script": "scripts/synth/time_serial.ys"
}
```

Es la entrada real de la variante temporal serial (B02). `smoke` falla si se registra una variante sin fuentes/testbench reales.

La variante `frequency_serial` registra siete módulos SystemVerilog de `frequency/`: tres bloques de datos, sus tres controles `*_control.sv` y `frequency_block_roms.sv` para las tablas combinacionales. Incluye su testbench y script Yosys. Adopta los formatos y redondeos A04, con comparación exacta contra el modelo Python y las columnas `yf` de los archivos oficiales A05: ver [C02, formatos y validación](../docs/frecuencia/arquitectura-rtl-frecuencia-serial.md#9-c02--adopción-de-a04-y-mejoras-futuras).

La variante `frequency_optimized` registra ocho módulos SystemVerilog en `frequency_optimized/`, incluido el top `fir_frequency_optimized`, junto con su testbench y script de síntesis. La integración C04 conserva la aritmética A04 y el contrato de ventanas, historial y handshakes descrito en [C04](../docs/frecuencia/c04-implementacion.md). La regresión integrada pasó 837 tramas A04/A05 con pausas, backpressure y reset; la latencia observada es L=26, con II de muestra 1 e II de bloque 8. Para la medición PPA SKY130 HD y sus límites, ver la [guía de frecuencia](../docs/frecuencia/ppa.md); el período RTL no implica cumplimiento físico.
