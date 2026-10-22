# PPA de los núcleos de frecuencia

El flujo local mide `frequency_serial` (C02) y `frequency_optimized` (C04) con
la biblioteca **SKY130 HD, 130 nm, TT 25 °C, 1,8 V**. Desde la raíz:

```sh
python3 scripts/ppa.py local --target frequency_serial
python3 scripts/ppa.py local --target frequency_optimized
python3 scripts/ppa.py package --target frequency_serial
python3 scripts/ppa.py package --target frequency_optimized
```

`local` ejecuta `smoke`, el benchmark de puertos y síntesis lógica SKY130.
`package` repite esa misma medición ASIC y además crea un ZIP para la posterior
referencia FPGA con Vivado en Windows; no reemplaza ni convierte la medición
ASIC en PPA FPGA. No se corre un target combinado: cada variante se selecciona
por separado. El resumen consultable es
[`reports/ppa/frequency.md`](../../reports/ppa/frequency.md); las instrucciones
del ZIP están en [`scripts/ppa/vivado/README.md`](../../scripts/ppa/vivado/README.md).

Después de sintetizar, el flujo simula `mapped.v` con Icarus y los modelos
funcionales de SKY130 (`FUNCTIONAL`, `UNIT_DELAY` vacío). Usa el mismo
benchmark de 2048 salidas y compara las salidas y métricas con la ejecución RTL.
Para resolver los modelos, deben estar junto al directorio `lib` de la
biblioteca seleccionada: `verilog/primitives.v` y
`verilog/sky130_fd_sc_hd.v`. La corrida copia ambos a `library_models/` y
registra sus hashes en el manifiesto. `gate_metrics.json` contiene las métricas
de esa simulación; `logs/gate_compile.log` y `logs/gate_benchmark.log` conservan
la compilación y ejecución.

La biblioteca se puede indicar con `--liberty PATH`; también se admite la
variable `SKY130_LIB`. Tienen prioridad el argumento y luego la variable. Si
ninguno se indica, el flujo busca versiones instaladas por Volare en
`~/.volare/volare/sky130/versions/*/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib`.
Si encuentra exactamente una, la usa; si no encuentra ninguna o hay varias,
indica el problema y requiere seleccionar la ruta con `--liberty`.

El benchmark RTL comprueba las salidas exactas y reporta ciclos, latencia y
throughput de simulación; la simulación funcional de `mapped.v` permite
contrastar ese comportamiento y esas métricas después del mapeo. Al ser zero-delay,
no modela retardos de celdas ni interconexión y no es simulación temporal con
SDF. La síntesis informa conteos de celdas, FF y área de celdas en µm² según la
biblioteca elegida. Estas medidas no incluyen STA,
ubicación y ruteo, ni potencia; por tanto no demuestran frecuencia física ni
cumplimiento de timing. Los períodos del testbench —100 ns para C02 y 10 ns
para C04— son parámetros de simulación y **no están validados físicamente**.

Cada corrida queda bajo `build/ppa/<target>/<corrida>/`, con su manifiesto,
métricas, celdas y logs. `frequency.md` mantiene para cada variante solo la
**última corrida local exitosa**: una corrida exitosa nueva reemplaza la entrada
previa aunque sus resultados sean equivalentes. Las ejecuciones fallidas no
desplazan la última exitosa; las evidencias anteriores permanecen en `build/`
o en la ubicación donde se hayan archivado.

## Referencia FPGA con Vivado

El ZIP de `package` conserva los fuentes, vectores, restricciones y scripts
necesarios para completar el flujo FPGA externo descrito en la guía Vivado.
Es un resultado aparte: timing, utilización y potencia FPGA requieren correr
Vivado y revisar sus evidencias. La sección histórica Vivado de C02 en
[`frequency.md`](../../reports/ppa/frequency.md) conserva sus condiciones y
procedencia; la nueva regla de última corrida local aplica a las mediciones
locales automatizadas, no reescribe esa historia.

Para la definición funcional y las limitaciones de C04, ver el
[contrato de implementación](c04-implementacion.md).
