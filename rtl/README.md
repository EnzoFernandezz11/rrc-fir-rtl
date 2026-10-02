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

Es un **ejemplo de formato**; esos archivos todavía no existen. `smoke` falla si se registra una variante sin fuentes/testbench reales.
