# Vivado en Windows

Para un ZIP de C04, usar primero la invocación específica del README en la raíz
del paquete: selecciona top, banco, período de 10 ns y ciclos medidos. Ejecutar
sin opciones selecciona la base serial de 100 ns descrita a continuación.

Extraer el ZIP completo y abrir una consola con Vivado en `PATH` (por ejemplo,
ejecutando `settings64.bat` de su instalacion). Desde la raiz del paquete:

```bat
scripts\ppa\vivado\run.bat
```

Opcionalmente, elegir una carpeta **nueva** de resultados:

```bat
scripts\ppa\vivado\run.bat "C:\resultados PPA\frequency_serial_01"
```

Para A07, el mismo flujo acepta otra variante mediante argumentos; sin opciones
conserva la configuracion serial de frecuencia. El lanzador Windows usa nombres
PowerShell y los convierte a las opciones Tcl indicadas:

| Windows (`run.bat`) | Tcl (`-tclargs`) | Valor por defecto |
|---|---|---|
| `-Top` | `-top` | `fir_frequency_serial` |
| `-Bench` | `-bench` | `tb_fir_frequency_ppa` |
| `-PeriodNs` | `-period_ns` | `100` |
| `-LatencyCycles` | `-latency_cycles` | `559` |
| `-BlockCycles` | `-block_cycles` | `575` |
| `-ActiveCycles` | `-active_cycles` | `147200` |
| `-Vectors` | `-vectors` | `vectors/ppa_vectors.txt` |

Ejemplo para repetir la base de frecuencia con argumentos explicitos:

```bat
scripts\ppa\vivado\run.bat "C:\resultados PPA\frequency_serial_02" -Top fir_frequency_serial -Bench tb_fir_frequency_ppa -PeriodNs 100 -LatencyCycles 559 -BlockCycles 575 -ActiveCycles 147200 -Vectors vectors/ppa_vectors.txt
```

Tambien se puede invocar Vivado directamente, sin el lanzador Windows:

```sh
vivado -mode batch -source scripts/ppa/vivado/run.tcl -tclargs build/ppa/frequency_serial/manual_01 -top fir_frequency_serial -bench tb_fir_frequency_ppa -period_ns 100 -latency_cycles 559 -block_cycles 575 -active_cycles 147200
```

Ejemplo completo para la serial temporal (A07), desde la raiz del repositorio:
generar los vectores del modelo temporal, correr Vivado a 10 MHz e importar la
corrida a la tabla. Para 100 MHz cambia solo `-period_ns 10`; los ciclos no
dependen del reloj. Con B04, ajustar `LATENCY`/`INTERVAL` en el banco y
`-latency_cycles`, `-block_cycles` y `-active_cycles = 2047 * II + L + 1`.

```sh
python3 -m scripts.ppa_vectors build/ppa/ppa_vectors_time.txt --domain time
vivado -mode batch -source scripts/ppa/vivado/run.tcl -tclargs build/ppa/time_serial/manual_01 -top fir_time_serial -bench tb_fir_time_ppa -period_ns 100 -latency_cycles 9 -block_cycles 10 -active_cycles 20480 -vectors build/ppa/ppa_vectors_time.txt
python3 -m scripts.ppa_table --import build/ppa/time_serial/manual_01 time_serial
python3 -m scripts.ppa_table
```

El flujo lee `rtl/*/*.sv` y busca un unico `tb/*/<Bench>.sv`. A07 debe aportar
el banco de la variante temporal y sus vectores de referencia; el banco temporal
funcional actual no implementa este protocolo PPA. Cada banco PPA debe instanciar
el nucleo como `dut`, aceptar `+VECTORS`, `+METRICS`, `+PERIOD_NS` y `+TIMING`,
y exponer `activity_window`, `benchmark_done` y `benchmark_pass` como el banco
de frecuencia. Los vectores conservan el workload de semilla 1, 1024 simbolos
y 2048 muestras, con la salida fija correspondiente a la variante. El JSON debe
incluir `output_samples`, `clock_period_ns`, `active_cycles`, `latency_cycles`,
`block_cycles` y `throughput_samples_per_second`. El periodo se aplica tanto al
XDC generado como a la simulacion; SAIF, SDF, Fmax y resumen usan la variante
elegida. Los limites de espera escalan con el periodo y los ciclos activos
esperados. `configuration.txt` registra estos ajustes y `summary.tsv` conserva
sus mismas filas para A07. `python3 scripts/ppa.py package --target frequency_optimized` empaqueta C04 con
su RTL, banco, vectores e invocación específica; sin `--target` empaqueta la base
serial.

No requiere Python. El lanzador usa PowerShell incluido en Windows para crear
la carpeta antes de iniciar Vivado y guardar `vivado.log` y `vivado.jou` completos.
Requiere Vivado con soporte de Artix-7 y sus herramientas
`xvlog`, `xelab` y `xsim`; registra la version realmente utilizada. Por defecto,
guarda en `build/ppa/frequency_serial/<UTC>-<commit>-vivado/`. Nunca sobrescribe
una corrida existente. Para leer los resultados, abrir **`summary.md`** de esa
carpeta: contiene las metricas finales y la referencia local anterior. Tras
revisarlo, incorporar la última medición FPGA identificando su corrida de origen
en `reports/ppa/frequency.md`, separada de las mediciones ASIC SKY130. Respetar
la regla del informe: última corrida por variante y tecnología, sin acumular
resúmenes; conservar la referencia histórica Vivado C02 expresamente indicada.

El resumen tambien incluye el diagnostico para elegir C03/C04: desglose de
ciclos del serial, peor camino interno de setup (`timing_critical.rpt`) y
recursos por jerarquia. Leer origen/destino, retardo de logica/ruteo y modulos
dominantes antes de proponer cambios; `power.rpt` permite revisar el costo
dinamico por recurso. El texto de analisis incluido esta en `diagnosis.txt`, extraido del registro
comun `reports/ppa/frequency.md` al preparar el paquete.

El flujo sintetiza e implementa `fir_frequency_serial` out-of-context para
`xc7a35tcpg236-1`, con reloj de 100 ns y opciones por defecto. Guarda utilizacion,
setup/hold internos, caminos sin constraints, DRC, checkpoint, netlist y SDF.
La estimacion de Fmax usa `1000 / (periodo_ns - WNS)` MHz; no reemplaza un barrido de
frecuencias ni verifica las interfaces fisicas de la placa. Este paquete analiza
el nucleo sin asignacion de pines ni restricciones temporales de E/S.

La simulacion temporal usa SDF slow/max y compara las 2048 salidas contra los
vectores A04 incluidos. `simulate.tcl` abre y cierra SAIF en los cambios exactos
de `activity_window` del banco: excluye reset y ciclos finales de guarda, e
incluye copia de historia, captura, calculo y emision. Verifica `benchmark_pass`
antes de crear `simulation_passed.txt`. STA informa setup y hold; este paquete
no ejecuta las cuatro combinaciones de esquina y columna SDF.

`read_saif.rpt` conserva el resumen oficial de correspondencia;
`unmatched_saif.rpt` enumera las redes sin correspondencia;
`switching_activity.rpt` conserva la fuente de actividad por red. La potencia
queda marcada para revisar esa cobertura, ya que redes sin anotacion pueden
usar actividad estimada. `power.rpt` separa potencia dinamica y estatica; la
estatica corresponde al dispositivo completo. `operating_conditions.rpt`
registra las condiciones termicas y electricas por defecto de la version usada.
La energia por muestra es potencia dinamica / throughput medido en esa ventana.

`manifest.json` del paquete identifica commit, cambios locales y hashes de las
entradas; se copia como `source_manifest.json`. Describe el paquete base, no
la corrida: dos corridas del mismo paquete a 10 y 100 MHz tienen el mismo
`source_manifest.json`. La configuracion efectiva de cada corrida (top, banco,
periodo, ciclos esperados, vectores) esta en `configuration.txt`; para saber a
que reloj se midio una fila, leer `clock_period_ns` ahi. `file_sizes.tsv` enumera el
tamano de los archivos generados antes de escribir el propio inventario.
Una corrida incompleta deja `run_status.txt`, `failure.txt` y `summary.md`;
consultar tambien los logs de compilacion, elaboracion y simulacion.

Estos scripts se revisaron y sus parsers se probaron con Tcl local. La
compatibilidad con la version de Vivado del companero y los resultados fisicos
requieren ejecutar esta entrega en esa PC.

Referencias AMD: [netlist temporal](https://docs.amd.com/r/2020.2-English/ug900-vivado-logic-simulation/Generating-a-Timing-Netlist),
[camino de timing detallado](https://docs.amd.com/r/2021.2-English/ug835-vivado-tcl-commands/report_timing),
[opciones de xelab](https://docs.amd.com/r/2023.1-English/ug900-vivado-logic-simulation/xelab-xvhdl-and-xvlog-xsim-Command-Options),
[condiciones de simulacion](https://docs.amd.com/r/2022.1-English/ug835-vivado-tcl-commands/add_condition),
[generacion SAIF](https://docs.amd.com/r/2022.2-English/ug900-vivado-logic-simulation/Generating-SAIF-Dumping),
[importacion SAIF](https://docs.amd.com/r/2021.1-English/ug835-vivado-tcl-commands/read_saif),
[condiciones de potencia](https://docs.amd.com/r/2023.2-English/ug907-vivado-power-analysis-optimization/Device-Environment).
