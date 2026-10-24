# PPA de los núcleos de frecuencia

## Implementación física OpenLane 2

Metodología adoptada para C02/C04: OpenLane 2 mediante Nix, siguiendo los
módulos 7–10 y la guía de instalación del curso. El checkout debe estar limpio
y fijado en a7b0e6d (2.3.10-1); PDK Volare
0fe599b2afb6708d281543108caf8310912f54af, sky130A, sky130_fd_sc_hd.
Los ejemplos con flow.tcl son de OpenLane 1 y no se copian literalmente.

El perfil Nix del repositorio reutiliza los mismos motores del checkout fijado,
excluyendo las dependencias directas KLayout/Magic/Netgen y sus pruebas de
paquete, que no se ejecutan hasta STA. No cambia los motores de síntesis,
ruteo ni STA. Evita compilar dos variantes de KLayout al preparar este análisis.
Se valida con SPM y las regresiones del proyecto; el hash del perfil queda
registrado en cada medición. El entorno completo del curso también es válido,
pero requiere más dependencias y espacio de instalación en /nix.

Usar el caché firmado FOSSi para evitar compilar los motores en el disco raíz.
En instalaciones Determinate, añadir el contenido revisable de
scripts/ppa/openlane/nix-cache.conf a /etc/nix/nix.custom.conf y reiniciar
nix-daemon con privilegios administrativos. La clave pública completa está en
la [guía oficial Nix-EDA](https://github.com/fossi-foundation/nix-eda/blob/main/docs/installation.md);
la copia PDF del curso la muestra truncada. No desactivar la verificación de firmas.

Desde la raíz, conservando el Python que tiene las dependencias del proyecto:

~~~sh
sh scripts/ppa/openlane/run.sh --target frequency_serial
sh scripts/ppa/openlane/run.sh --target frequency_optimized
~~~

OPENLANE_ROOT permite indicar el checkout y PPA_PYTHON el intérprete local.
Si ya se está dentro del entorno fijado:

~~~sh
python3 scripts/ppa.py physical --target frequency_serial
python3 scripts/ppa.py physical --target frequency_optimized
~~~

El comando valida primero el ejemplo SPM en build/ppa/openlane-preflight/.
Luego ejecuta la regresión/benchmark local sin publicar todavía y ejecuta
OpenLane Classic hasta OpenROAD.STAPostPNR: síntesis, floorplan, placement,
CTS, ruteo y extracción RC. Se usan utilización 35 %, densidad 45 %,
estrategia AREA 0, dos hilos y sin retiming de ABC. No agrega clock gating.
No se ejecuta el signoff completo de fabricación (GDS/DRC Magic/LVS); no se
presenta este resultado como chip listo para fabricar.

Los objetivos son 100 ns para C02 y 10 ns para C04. El SDC base de esta versión
incluye E/S y reset síncrono, cargas, incertidumbre y transición; el SDC resuelto
queda en los artefactos. STA cubre las nueve combinaciones de TT/SS/FF y
RC nom/min/max, con reloj propagado y SPEF. Se registran slacks positivos y WNS
(limitado a cero), TNS, violaciones, advertencias de restricciones y redes
ruteadas sin parasíticos. PASS exige setup/hold sin violaciones en todos los
corners, restricciones completas y parasíticos de todas las redes ruteadas.
Fmax es una estimación registro a registro: no es un barrido de frecuencia ni
demuestra por sí sola timing de E/S.

Cada corrida verifica la netlist final con las mismas 2048 muestras. El nuevo
argumento +POWER_VCD=archivo guarda la actividad completa; +VCD=archivo
conserva el volcado corto habitual. Se recorta/rebasa la ventana activa en
streaming porque el OpenSTA fijado no soporta los selectores de tiempo de
versiones recientes. Reset y guarda final quedan fuera del análisis.

Potencia usa netlist final, Liberty TT/25 °C/1,8 V, SDC resuelto, SPEF nominal y
read_vcd con scope del DUT. El volcado incluye los pines de las celdas. Se exige
actividad de origen VCD, reloj o constante en todos los pines y se registra el
conteo real importado por OpenSTA; no es cobertura funcional. Se cubren pines
externos de celdas y puertos del top: los estados internos Liberty IQ/IQ_N
no son puertos Verilog y se cuentan aparte, fuera del denominador.
Se informa la actividad **funcional
sin retardos**, que no reproduce todos los glitches temporales.
Se distinguen interna, switching, dinámica (= interna + switching), leakage y
total. Energía = potencia × duración activa / 2048.

El escenario target usa el objetivo propio. common repite STA y actividad a
10 MHz sobre el mismo layout, sin repetir P&R. Las métricas físicas están en
physical_metrics.json; los estados OpenLane enlazan netlist, ODB, DEF, SDC,
SPEF y SDF. El SDF se exporta; su simulación es adicional, no obligatoria.
Una corrida completa puede informar timing FAIL; una falla de herramienta o
evidencia incompleta conserva la última medición publicada.

## Comparación reproducible y gráficos Mermaid

Después de obtener las dos corridas, indicar sus directorios explícitos:

~~~sh
python3 scripts/ppa.py compare --c02 build/ppa/frequency_serial/CORRIDA --c04 build/ppa/frequency_optimized/CORRIDA --render
~~~

Sin --render se generan los bloques Mermaid y fuentes .mmd sin necesitar
Node. --render exporta SVG con @mermaid-js/mermaid-cli@11.6.0 y Chromium
mediante npm; requiere red la primera vez. Node/npm sólo son necesarios para
exportar/verificar SVG. La configuración Puppeteer desactiva su sandbox para
este render local controlado. Los radares requieren Mermaid ≥11.6.0; el informe
enlaza SVG como alternativa a visores incompatibles.

Se leen los JSON/manifiestos, nunca los números del Markdown. Se exige la misma
etapa, biblioteca, herramientas, benchmark y método físico. Las corridas deben
ser las publicadas; una actualización invalida la comparación anterior.
Los artefactos quedan en build/ppa/comparisons/ con identidad de sus entradas.

La tabla enumera todas las métricas, unidades, cambios y procedencia; los
valores sin evidencia dicen “No medida”. Barras individuales evitan mezclar
unidades y separan relojes propios de 10 MHz común. Timing conserva sus signos
y corners. No se comparan cifras ASIC con Vivado.

El radar arquitectónico agrupa área Liberty, FF, latencia e intervalo por bloque.
El radar físico agrupa área final, latencia temporal, throughput efectivo y
energía total a 10 MHz, sólo si ambas implementaciones pasan STA en ese escenario.
100 significa el mejor valor de la pareja por eje: beneficios =
100 × valor/máximo; costos = 100 × mínimo/valor. Empates en cero reciben 100;
costo cero frente a positivo recibe 100 frente a 0. No hay nota global ni se
interpreta la superficie como “ganador”. Datos faltantes eliminan el eje en
ambas curvas; menos de tres ejes omite el radar.

## Medición lógica local

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
