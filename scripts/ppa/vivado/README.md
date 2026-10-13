# Vivado en Windows

Extraer el ZIP completo y abrir una consola con Vivado en `PATH` (por ejemplo,
ejecutando `settings64.bat` de su instalacion). Desde la raiz del paquete:

```bat
scripts\ppa\vivado\run.bat
```

Opcionalmente, elegir una carpeta **nueva** de resultados:

```bat
scripts\ppa\vivado\run.bat "C:\resultados PPA\frequency_serial_01"
```

No requiere Python. El lanzador usa PowerShell incluido en Windows para crear
la carpeta antes de iniciar Vivado y guardar `vivado.log` y `vivado.jou` completos.
Requiere Vivado con soporte de Artix-7 y sus herramientas
`xvlog`, `xelab` y `xsim`; registra la version realmente utilizada. Por defecto,
guarda en `build/ppa/frequency_serial/<UTC>-<commit>-vivado/`. Nunca sobrescribe
una corrida existente. Para leer los resultados, abrir **`summary.md`** de esa
carpeta: contiene las metricas finales y la referencia local anterior. Tras
revisarlo, incorporar los resultados a la corrida correspondiente del registro
`reports/ppa/frequency.md` en el repositorio, conservando el historial serial y
la seccion de la variante optimizada.

El resumen tambien incluye el diagnostico para elegir C03/C04: desglose de
ciclos del serial, peor camino interno de setup (`timing_critical.rpt`) y
recursos por jerarquia. Leer origen/destino, retardo de logica/ruteo y modulos
dominantes antes de proponer cambios; `power.rpt` permite revisar el costo
dinamico por recurso. El texto de analisis incluido esta en `diagnosis.txt`, extraido del registro
comun `reports/ppa/frequency.md` al preparar el paquete.

El flujo sintetiza e implementa `fir_frequency_serial` out-of-context para
`xc7a35tcpg236-1`, con reloj de 100 ns y opciones por defecto. Guarda utilizacion,
setup/hold internos, caminos sin constraints, DRC, checkpoint, netlist y SDF.
La estimacion de Fmax usa `1000 / (100 - WNS)` MHz; no reemplaza un barrido de
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
entradas; se copia como `source_manifest.json`. `file_sizes.tsv` enumera el
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
