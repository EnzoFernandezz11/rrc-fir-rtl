# PPA del núcleo serial de frecuencia

El flujo mide `fir_frequency_serial` completo. En la PC local se verifican las salidas, se miden ciclos y se obtiene un mapeo lógico para Artix-7. El paquete para Windows completa implementación, simulación temporal y estimación de potencia en Vivado.

Esta primera medición establece la **base serial para decidir C03/C04**. El
registro incluye el [análisis de la base serial](../../reports/ppa/frequency.md#análisis-base-serial): distribución
de ciclos, preguntas para localizar el costo y criterios para elegir la próxima
optimización. El resumen de Vivado incorpora además el peor camino interno de
setup y los recursos por jerarquía. La comparación con la variante optimizada se
hará después, contra esta base y declarando las condiciones de ambas corridas.

## Configuración de esta corrida

| Parámetro | Valor |
|---|---|
| FPGA | Basys3, Artix-7 `xc7a35tcpg236-1` |
| Reloj | 10 MHz, período de 100 ns |
| Implementación | Núcleo **out-of-context**, sin pines de placa; estrategias por defecto |
| Constraints | [`clk_10mhz.xdc`](../../constraints/clk_10mhz.xdc), solo reloj |
| Formatos A04 | Entrada 2 bits/F=0; trabajo 12/F=5; coeficientes 10/F=8; salida 9/F=7 |
| Estímulo | QPSK con sobremuestreo 2×, semilla 1, 1024 símbolos: 2048 muestras |
| Interfaz | Entrada disponible y salida siempre lista |
| Reset | Síncrono activo alto, diez ciclos iniciales |
| Referencia | Modelo fijo A04, comparación exacta de I y Q por índice de salida |

Estos son los ajustes de este flujo local. A05 está integrado y C02 compara sus archivos oficiales en `make smoke`. El testbench PPA dedicado conserva su formato local A04; su adopción del formato A05 y la aprobación conjunta del [contrato PPA](../contratos/verificacion-y-ppa.md) siguen pendientes. Las corridas históricas conservan su procedencia y no cambian el estado de ese contrato.

## Ejecutar en la PC local

Desde la raíz del repositorio, con Python y las dependencias del modelo, Icarus Verilog y Yosys disponibles:

```sh
make ppa-local
```

El comando ejecuta la regresión `smoke`, genera los vectores y corre un testbench dedicado que usa solamente los puertos del núcleo para comprobar sus resultados. Después sintetiza con `synth_xilinx -family xc7 -flatten -noiopad -noclkbuf`. Es el mismo enfoque de los ejercicios del curso: Icarus para comprobar comportamiento y ciclos, GTKWave para inspección, y Yosys para contar recursos mapeados.

Cada ejecución crea `build/ppa/frequency_serial/<fecha-commit>/` y muestra su ruta. Los archivos principales son:

| Archivo | Contenido |
|---|---|
| `manifest.json` | Configuración, revisión, herramientas, hashes y tamaños de artefactos |
| `local_metrics.json` | Contadores y medidas del benchmark |
| `resources.json` | Conteos agrupados de primitivas Xilinx |
| `cells.json` | Estadísticas originales de Yosys |
| `first_blocks.vcd` / `first_blocks.gtkw` | Ondas limitadas a los primeros cuatro bloques y selección de señales |
| `logs/` | Comandos y diagnósticos de las herramientas |
| `summary.md` | Copia del resumen de la corrida; el informe de consulta está en `reports/ppa/frequency.md` |

Para inspeccionar las ondas, reemplazar `<fecha-commit>` por la corrida indicada:

```sh
gtkwave build/ppa/frequency_serial/<fecha-commit>/first_blocks.gtkw
```

Se exige recibir exactamente las 2048 salidas correctas, sin pérdidas ni duplicados, y comprobar el presupuesto ideal de **559 ciclos de latencia** y **575 ciclos por bloque de ocho muestras**. El throughput se calcula con los contadores efectivos del benchmark y el período de 100 ns. Las ondas permiten revisar los primeros bloques sin guardar toda la actividad de la prueba.

Los conteos de LUT, FF, DSP, BRAM, CARRY y multiplexores dedicados de Yosys son **mapeo lógico preliminar**. Se conservan las categorías por separado. Todavía faltan ubicación y ruteo para informar timing físico y potencia.

## Preparar el envío a Windows

```sh
make ppa-package
```

Este comando vuelve a ejecutar la validación local y genera `frequency_serial_vivado.zip` dentro de la nueva corrida, para que los vectores, fuentes y resultados correspondan entre sí. El ZIP contiene RTL, testbench, vectores ya calculados, XDC, scripts Tcl, lanzador Windows e instrucciones. La PC de Vivado no necesita Python. Ondas, checkpoints y cachés locales quedan fuera del paquete.

Tu compañero debe extraer el ZIP y, desde su carpeta raíz, ejecutar el lanzador en una consola de Windows que tenga `vivado` disponible:

```bat
scripts\ppa\vivado\run.bat
```

Puede indicar una carpeta de resultados como argumento, entre comillas si tiene espacios. La versión realmente utilizada se registra en `tool_versions.txt`.

El flujo Vivado acepta top, banco, período y ciclos esperados por argumentos para
que A07 pueda reutilizarlo. Las [opciones y el contrato del banco PPA](../../scripts/ppa/vivado/README.md)
detallan cómo incorporar otra variante; los valores por defecto conservan esta
base serial de frecuencia y el formato de `summary.tsv`.

El flujo de Vivado realiza:

1. Síntesis e implementación out-of-context para `xc7a35tcpg236-1` a 100 ns.
2. Reportes de utilización, timing, caminos críticos y restricciones faltantes.
3. Exportación del diseño implementado, netlist temporal y SDF.
4. Simulación temporal con xsim del mismo vector y comprobación de todas las salidas.
5. Captura de SAIF durante el procesamiento, excluyendo reset e incluyendo captura, copia de historial, cálculo y emisión.
6. Importación de SAIF y `report_power`, registrando cobertura de anotación y señales sin correspondencia.

La estimación de potencia usa actividad del diseño implementado, como describe el [flujo SAIF de AMD](https://docs.amd.com/r/2022.2-English/ug997-vivado-power-analysis-optimization-tutorial/Step-3-Running-Report-Power-with-Vivado-Simulator-SAIF-Data). Una anotación incompleta debe revisarse antes de usar la cifra como resultado comparable. Se conservan las condiciones de operación y temperatura utilizadas por Vivado.

## Leer y conservar los resultados

| Métrica | Lectura |
|---|---|
| Área final | LUT, FF, DSP48 y BRAM del diseño implementado en Vivado |
| Cumplimiento del reloj | WNS ≥ 0 a 100 ns; revisar además hold y caminos sin constraints |
| Fmax estimada | `1000 / (100 − WNS_ns)` MHz, usando caminos internos de setup del reloj |
| Latencia | Ciclos entre aceptación de entrada y salida correspondiente, según los contadores de la prueba |
| Throughput | Muestras procesadas / duración medida en segundos |
| Potencia | Dinámica y estática por separado, en W, con procedencia y cobertura del SAIF |
| Energía por muestra | `P_dinámica_W / throughput_muestras_por_segundo`, en J/muestra |

La Fmax es una aproximación a partir de una implementación a 10 MHz; este flujo no hace un barrido de frecuencias. Los caminos externos no tienen presupuestos de entrada/salida porque el alcance acordado es medir el núcleo out-of-context con constraint de reloj.

**Para revisar los resultados, abrir un solo archivo: `reports/ppa/frequency.md`.** Contiene la configuración, las medidas locales y las secciones de Vivado; estas últimas quedan pendientes hasta recibir los resultados de Windows. Cada ejecución local registra las nuevas medidas en el historial serial sin duplicar ejecuciones equivalentes y conserva su copia original en `build/ppa/frequency_serial/<fecha-commit>/summary.md`.

Cuando tu compañero termine, su carpeta de resultados contendrá un `summary.md` con los resultados de Vivado primero y las medidas locales del paquete como referencia. Después de revisarlo, incorporar sus medidas y conclusiones a la entrada local correspondiente en `reports/ppa/frequency.md`, o agregar una entrada Vivado identificando la corrida local de origen. Conservar las entradas anteriores y la ruta donde se archivaron las evidencias. Los enlaces internos del resumen recibido se deben ajustar a esa ubicación antes de incorporarlos.

Los archivos `utilization.rpt`, `timing_metrics.json`, `power.rpt`, `run_status.txt` y `read_saif.rpt`/`unmatched_saif.rpt` permiten auditar las cifras, el resultado de simulación y la cobertura SAIF. El registro común contiene el análisis base, las corridas seriales y una sección para las futuras corridas optimizadas.

Los archivos pesados permanecen en `build/ppa/frequency_serial/` o en una copia externa identificada. El manifiesto permite consultar tamaños reales antes de compartir artefactos.

La ejecución local deja timing y potencia como pendientes de Vivado. Los scripts de Windows requieren validación en la PC de tu compañero; que el paquete se genere correctamente no equivale a haber ejecutado Vivado.
