# Registro PPA en frecuencia

[Resultados y análisis de las corridas seriales y optimizadas](frequency.md).

El informe incluye tabla comparativa, barras Mermaid y radar normalizado
(100 = mejor valor por eje). Los gráficos actuales identifican su nivel de
evidencia; potencia y timing físicos no se rellenan con datos supuestos.
Cuando se genera con `--render`, los SVG permiten ver los radares en visores sin Mermaid ≥11.6.0.

El informe muestra, por variante, solo la última corrida local exitosa. Cada nueva corrida exitosa reemplaza la anterior aunque sea equivalente; sus artefactos completos quedan en `build/ppa/`. El subconjunto auditable está versionado en [`frequency_serial/sky130/`](frequency_serial/sky130/evidence.json) y [`frequency_optimized/sky130/`](frequency_optimized/sky130/evidence.json), con SHA256 y procedencia en `evidence.json`. Los gráficos y sus fuentes se publican bajo `comparisons/`. La historia de Vivado C02 se conserva en su sección histórica y no se reemplaza con la medición local SKY130.

Las instrucciones y limitaciones están en la [guía PPA](../../docs/frecuencia/ppa.md). La medición local usa SKY130 HD; `package` añade un ZIP para una referencia FPGA posterior con Vivado y no sustituye esa medición ASIC.

El método común SKY130 para las cuatro variantes está acordado en D05/D06.
El cumplimiento de setup/hold se evalúa en los nueve corners; slew, capacitancia
y fanout se presentan por separado. La tabla A07 se consolidará con B04;
los reportes y scripts Vivado se conservan como referencia FPGA.
