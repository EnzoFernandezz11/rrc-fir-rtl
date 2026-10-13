# RTL

Ubicar las variantes temporal serial/optimizada en `time/`, y las variantes en frecuencia en `frequency/`. `common/` recibe solo módulos compartidos de verdad. Cada variante integrada debe añadirse a [`config/rtl_targets.json`](../config/rtl_targets.json) junto con su testbench y, cuando exista, script de síntesis.

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

Es un **ejemplo de formato**; esos archivos temporales todavía no existen. `smoke` falla si se registra una variante sin fuentes/testbench reales.

La variante `frequency_serial` registra siete módulos SystemVerilog de `frequency/`: tres bloques de datos, sus tres controles `*_control.sv` y `frequency_block_roms.sv` para las tablas combinacionales. Incluye su testbench y script Yosys. Adopta los formatos y redondeos A04, con comparación exacta contra el modelo Python: ver [C02, formatos y validación](../docs/arquitectura-rtl-frecuencia-serial.md#9-c02--adopción-de-a04-y-mejoras-futuras). Ejecutar `make smoke` y `make full` desde la raíz.
