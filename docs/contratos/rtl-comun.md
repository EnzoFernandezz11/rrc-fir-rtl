# Contrato RTL común: generación, entrada y salida

**Reparto:** aceptado por Enzo y Julián, confirmado por Enzo el 7/10/2026. **Interfaces y parámetros nuevos:** propuestas pendientes de acuerdo.

**Issue:** [R01 / #31](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/31).

## Objetivo

Implementar una sola vez los bloques RTL de entrada y salida independientes del filtro y reutilizarlos en las cadenas temporal y en frecuencia. Cada autor diseña por separado el núcleo completo de su filtro.

```text
Generador QPSK → upsampler 2× → adaptador de entrada → filtro → salida común
```

## Responsables y reparto acordado

**Enzo confirmó el 7/10/2026 que Julián aceptó este reparto.** La aceptación corresponde a las responsabilidades; no convierte en aprobadas las propuestas de reset, formato, fuente de bits, control de trama o latencias detalladas más abajo.

| Módulo | Responsable | Revisor e integración en la otra cadena |
|---|---|---|
| Generador QPSK RTL `qpsk_symbol_gen` | @moreyrajulian | @EnzoFernandezz11 |
| Upsampler `upsampler_2x` | @EnzoFernandezz11 | @moreyrajulian |
| Adaptador/wrapper `sample_input_adapter` | @EnzoFernandezz11 | @moreyrajulian |
| Etapa común `sample_output_stage` | @moreyrajulian | @EnzoFernandezz11 |

Cada responsable entrega su RTL y testbench; el otro revisa el contrato e integra el bloque en su cadena. Si el adaptador de entrada es una conexión directa, puede formar parte del wrapper en lugar de requerir un módulo independiente.

## Alcance

Compartir código con instancias independientes: generación de símbolos, upsampling 2× y presentación/aceptación de muestras I/Q en entrada y salida.

Para esta tarea se asumen suministrados los coeficientes y formatos. La preparación de esas tablas no es un entregable de esta tarea. Los multiplicadores, memorias h/H/W, redondeos internos, MAC, FFT/IFFT, historial, procesamiento por bloques y FSM de los núcleos quedan a cargo de cada autor, fuera del reparto común.

La salida común recibe resultados ya calculados, seleccionados y convertidos al formato externo. No normaliza IFFT ni ejecuta operaciones del filtro. La transferencia de datos debe distinguir ceros válidos de burbujas.

## Dependencias y relación con otras tareas

- **Para empezar implementación definitiva:** E03 (#4), que fija el contrato externo consumiendo los formatos de E02 (#3). La discusión y preparación del contrato de esta tarea pueden avanzar antes; no implementar puertos definitivos basándose en valores pendientes.
- **Para cerrar:** integración y pruebas en B02 (#12) y C02 (#14). Esta tarea puede desarrollarse en paralelo con esas implementaciones y aporta sus bloques comunes; no exige esperar su cierre para comenzar los núcleos.
- B01 (#11) y C01 (#13) deben contemplar las latencias/capacidades acordadas. A06 (#15) podrá reutilizar las interfaces; sus tareas no se trasladan a este reparto.
- Plan local: R01, entrada/salida RTL común; actualizar backlog y Gantt con la tarea y sus dependencias.

## Contrato de conexión y fichas de cada módulo


**Interfaces y temporización propuestas, pendientes de acuerdo. El reparto de responsables ya está aceptado.** La función del contrato es que cada autor conozca los puertos y el comportamiento del vecino antes de implementar. Proponemos los nombres y reglas siguientes, sin fijar todavía valores de anchos ni el algoritmo de la fuente de bits.

### Datos, reloj y reset

- Un reloj `clk`, flanco ascendente. Propuesta: `rst` síncrono activo alto, común a toda la cadena; durante reset no hay transferencias, `valid=0` y se cancelan datos pendientes. El receptor puede mantener `ready=0` durante reset. Definir la inicialización de la secuencia del generador.
- I y Q viajan simultáneamente en puertos separados, como enteros **con signo en complemento a dos**.
- Entrada: parámetros comunes `W_IN` y `F_IN`, ancho por componente y bits fraccionarios. Valor real = entero almacenado / `2^F_IN`. Generador y upsampler usan el mismo formato, sin conversiones ocultas. Para representar ±1 exactamente, exigir `F_IN≥0` y `W_IN≥F_IN+2`: +1 se codifica como `+2^F_IN`, −1 como `−2^F_IN`, cero como todos los bits a cero.
- Salida: parámetros comunes `W_OUT` y `F_OUT`, también por componente. Cada núcleo entrega sus resultados ya convertidos a este formato; la salida común los conserva sin cambiar escala ni redondeo.
- Propuesta de trama: `last` acompaña al dato. No son decisiones aceptadas todavía el tipo de reset, el marcador de trama ni los valores de W/F; hay que cerrar esos puntos antes de implementar la versión definitiva.

### Enlaces entre módulos

Cada módulo consumidor tiene `in_i`, `in_q`, `in_valid`, `in_last` como entradas y `in_ready` como salida. Cada productor tiene `out_i`, `out_q`, `out_valid`, `out_last` como salidas y `out_ready` como entrada. Los nombres de los cables conectores pueden diferir; los nombres de puertos propuestos son uniformes.

| Enlace | Salidas del productor → entradas del consumidor | Señal de retorno | Ancho de I y Q / significado de `last` |
|---|---|---|---|
| Generador → upsampler | `gen.out_i/q/valid/last` → `up.in_i/q/valid/last` | `up.in_ready` → `gen.out_ready` | `W_IN`; marca el último símbolo de la trama |
| Upsampler → entrada del núcleo, directa o mediante adaptador | `up.out_i/q/valid/last` → `core.in_i/q/valid/last` | `core.in_ready` → `up.out_ready` | `W_IN`; marca el cero válido posterior al último símbolo |
| Núcleo → salida común | `core.out_i/q/valid/last` → `tx.in_i/q/valid/last` | `tx.in_ready` → `core.out_ready` | `W_OUT`; marca la última muestra calculada de la trama |
| Salida común → receptor externo | `tx.out_i/q/valid/last` → receptor | Receptor → `tx.out_ready` | `W_OUT`; conserva la misma marca de fin de trama |

Si hay un registro adaptador entre dos bloques, termina un enlace y origina otro con estas mismas señales. Debe conservar formato, orden y metadatos. Los puertos de los dos núcleos son iguales aunque internamente procesen de forma diferente.

### Reglas por ciclo

1. Se acepta el paquete `{i, q, last}` en un flanco ascendente solo con `valid && ready` fuera de reset. El productor anuncia datos disponibles sin esperar `ready`.
2. Si `valid=1 && ready=0`, conservar `valid`, I/Q y `last` hasta aceptación o reset. Datos y `last` no tienen significado cuando `valid=0`.
3. El generador avanza el índice de símbolo únicamente al aceptarse su salida. Si mantiene un PRNG, su siguiente símbolo visible no depende de la duración de las pausas.
4. Por cada símbolo aceptado, el upsampler entrega exactamente dos muestras aceptadas: primero el símbolo con `last=0`, después cero I/Q con `last` igual al del símbolo. No termina esa operación cuando solo presenta el cero: espera su aceptación.
5. Propuesta simple de capacidad del upsampler: un símbolo almacenado; no aceptar otro hasta entregar el cero pendiente. Latencia mínima propuesta: primera muestra disponible en el ciclo posterior a aceptar el símbolo; después puede entregar el cero en el ciclo posterior a aceptar la primera. Las pausas alargan esos tiempos. No exigir dos muestras en dos ciclos si el núcleo está detenido.
6. El núcleo conserva índices y metadatos pese a su latencia. Para una trama de S símbolos emite 2S resultados causales, sin cola adicional, y coloca `out_last` solo en el último. Frecuencia resuelve selección IFFT y padding antes de esta frontera.
7. Propuesta de salida común: registro de una muestra, sin paso combinacional de datos; puede reemplazar la muestra en el mismo flanco en que el receptor acepta la anterior. Latencia mínima de un ciclo y hasta una transferencia por ciclo en régimen; si se elige solo una conexión, registrar explícitamente esa alternativa en el contrato.

Ejemplo de **último símbolo** `a=1−j`, expresado en valores numéricos:

| Transferencia aceptada | I | Q | `last` |
|---|---:|---:|---:|
| Generador → upsampler | +1 | −1 | 1 |
| Upsampler → núcleo, primera muestra | +1 | −1 | 0 |
| Upsampler → núcleo, segunda muestra | 0 | 0 | 1 |

Entre esas transferencias puede haber cualquier número de ciclos de pausa. Si se detiene el cero final, sigue presentado con `valid=1` y `last=1`; el fin de trama se reconoce al aceptarlo.

### Entradas de control del generador

Propuesta para una fuente de tramas finitas: `start_valid` y `start_ready`, con `symbol_count[LEN_W−1:0]` y `seed[SEED_W−1:0]` como entradas de configuración. Aceptar el comando con `start_valid && start_ready`; capturar longitud/semilla, generar exactamente esa cantidad de símbolos y marcar el último con `out_last`. El emisor del comando mantiene configuración estable mientras espera aceptación.

El generador no acepta otro comando mientras tenga símbolos pendientes de la trama actual; vuelve a admitirlo después de aceptar el último símbolo. El upsampler puede seguir entregando su cero y frenar la nueva trama. Cada núcleo debe terminar la trama anterior y preparar su historial antes de aceptar muestras de una nueva trama independiente. El generador no decide cuándo termina la salida del filtro.

Falta elegir fuente de bits y significado/ancho de semilla. Propuesta inicial: aceptar solo `symbol_count>0`; **trama vacía pendiente de protocolo de control**, porque no existe una transferencia donde adjuntar `last`. Si se necesitan señales `busy/done`, acordar si indican fin de generación o fin de toda la cadena; no confundir ambos eventos.

### Qué debe quedar cerrado antes de implementar las interfaces definitivas

Un acuerdo escrito sobre reset, `last`/tramas vacías, W/F externos, configuración y fuente de bits, capacidad/latencia del upsampler y de la salida. Añadir un cronograma con pausas y nombres definitivos de puertos. Tras la aceptación, llevar esta sección al contrato permanente E03 y a la issue; los detalles internos del FIR y la FFT siguen a cargo de sus respectivos autores.

## Contrato individual de cada módulo común

Estas fichas concretan la propuesta anterior. Los nombres de módulos/archivos y los comportamientos nuevos son **propuestos**, no decisiones ya aceptadas. Todos los controles son de un bit salvo que se indique ancho; I/Q son `signed`. Los parámetros W/F deben tener el mismo valor a ambos lados de cada enlace.

### C1 — Generador: `qpsk_symbol_gen`

**Archivo tentativo:** `rtl/common/qpsk_symbol_gen.sv`. **Responsable acordado:** Julián. **Revisor/integración frecuencia:** Enzo.

| Parte | Puertos / parámetros |
|---|---|
| Parámetros | `W_IN`, `F_IN`, `LEN_W`, `SEED_W`; valores pendientes |
| Entradas comunes | `clk`, `rst` |
| Entradas de comando | `start_valid`, `symbol_count[LEN_W-1:0]`, `seed[SEED_W-1:0]` |
| Entrada desde upsampler | `out_ready` |
| Salidas de comando | `start_ready` |
| Salidas hacia upsampler | `out_i`, `out_q`: signed `[W_IN-1:0]`; `out_valid`, `out_last` |

**Obligación:** por comando aceptado, emitir `symbol_count` símbolos y marcar el último; no repetir ni saltar símbolos durante pausas. El contenido QPSK no conoce el filtro. Propuesta de mapeo para cerrar: bit 1 determina signo de I y bit 0 signo de Q, 0 → +1 y 1 → −1. Fuente de bits, semilla y primer símbolo deben ser reproducibles y quedar especificados antes de implementar.

**Temporización/capacidad:** una trama de generación activa; no aceptar otra hasta transferir el último símbolo. Fijar `L_GEN`, ciclos desde comando aceptado hasta primera salida disponible, y la tasa sin pausas. La disponibilidad de la primera salida no debe depender de esperar `out_ready`.

**Prueba de aceptación:** longitud exacta, los cuatro símbolos con el mapeo acordado, mismo resultado con la misma semilla pese a pausas, `last` estable y una sola vez, reset cancela la generación. El caso de longitud cero sigue pendiente.

### C2 — Upsampler: `upsampler_2x`

**Archivo tentativo:** `rtl/common/upsampler_2x.sv`. **Responsable acordado:** Enzo. **Revisor/integración temporal:** Julián.

| Parte | Puertos / parámetros |
|---|---|
| Parámetros | `W_IN`, `F_IN` |
| Entradas comunes | `clk`, `rst` |
| Entradas desde generador | `in_i`, `in_q`: signed `[W_IN-1:0]`; `in_valid`, `in_last` |
| Entrada desde adaptador/núcleo | `out_ready` |
| Salida hacia generador | `in_ready` |
| Salidas hacia adaptador/núcleo | `out_i`, `out_q`: signed `[W_IN-1:0]`; `out_valid`, `out_last` |

**Obligación:** capturar I/Q y `last` juntos; entregar el símbolo con `out_last=0` y luego cero con la marca capturada. Ambas son transferencias válidas independientes. Mantener fase y datos si la salida se detiene.

**Temporización/capacidad propuesta:** un símbolo almacenado; primera muestra disponible en el ciclo posterior a su aceptación. Después de aceptar esa muestra, el cero puede presentarse en el ciclo siguiente. `in_ready=0` mientras haya símbolo/cero pendientes; admitir el próximo símbolo en el ciclo posterior a aceptar el cero. En esta versión simple, sin pausas, se acepta como máximo un símbolo cada tres ciclos; produce dos muestras por símbolo, sin prometer flujo continuo de una muestra por ciclo. Una versión que acepte el siguiente símbolo en el mismo flanco del cero requiere otro acuerdo.

**Prueba de aceptación:** S símbolos → 2S muestras, orden símbolo/cero, pausa en cada fase y sobre el último cero, exactamente un `last` por trama no vacía, reset descarta el símbolo pendiente.

### C3 — Adaptador de entrada: `sample_input_adapter`

**Archivo tentativo:** `rtl/common/sample_input_adapter.sv`, si hace falta un archivo separado; puede integrarse en el wrapper. **Responsable acordado:** Enzo. **Revisor/integración temporal:** Julián.

| Parte | Puertos / parámetros |
|---|---|
| Parámetros | `W_IN`, `F_IN` |
| Entradas comunes | `rst`; `clk` si se adopta almacenamiento registrado |
| Entradas desde upsampler | `in_i`, `in_q`: signed `[W_IN-1:0]`; `in_valid`, `in_last` |
| Entrada desde núcleo | `out_ready` |
| Salida hacia upsampler | `in_ready` |
| Salidas hacia núcleo | `out_i`, `out_q`: signed `[W_IN-1:0]`; `out_valid`, `out_last` |

**Obligación:** transmitir exactamente el mismo paquete sin cambiar valores, orden, escala ni marca de trama. No arma bloques, no guarda historial del filtro y no decide cuándo el núcleo termina una trama.

**Base propuesta:** conexión directa, sin capacidad de almacenamiento y latencia cero: `out_i/q/last = in_i/q/last`, `out_valid = in_valid && !rst`, `in_ready = out_ready && !rst`. El upsampler conserva la muestra mientras espera. Si se necesita cortar un camino combinacional, acordar un registro de una muestra y registrar su capacidad y latencia de un ciclo; no cambiar la temporización del contrato silenciosamente.

**Prueba de aceptación:** mismo paquete aceptado a ambos lados y en el mismo flanco para la conexión directa; pausas propagadas, transferencias anuladas en reset, sin pérdida/duplicación. Para la alternativa registrada, comprobar conservación de orden y conteo con el ciclo adicional.

### C4 — Salida: `sample_output_stage`

**Archivo tentativo:** `rtl/common/sample_output_stage.sv`. **Responsable acordado:** Julián. **Revisor/integración frecuencia:** Enzo.

| Parte | Puertos / parámetros |
|---|---|
| Parámetros | `W_OUT`, `F_OUT` |
| Entradas comunes | `clk`, `rst` |
| Entradas desde núcleo | `in_i`, `in_q`: signed `[W_OUT-1:0]`; `in_valid`, `in_last` |
| Entrada desde receptor externo | `out_ready` |
| Salida hacia núcleo | `in_ready` |
| Salidas hacia receptor externo | `out_i`, `out_q`: signed `[W_OUT-1:0]`; `out_valid`, `out_last` |

**Obligación:** almacenar y entregar sin modificaciones cada muestra calculada y su `last`. Funciona igual para un flujo temporal o una ráfaga de frecuencia. La selección IFFT, el escalado y el formato numérico están resueltos por el núcleo antes de este módulo.

**Base propuesta:** registro de una muestra, inicialmente vacío; latencia mínima un ciclo, capacidad una muestra y una transferencia por ciclo sin pausas después de llenarse. Con `full` como estado de ocupación, `in_ready = !rst && (!full || out_ready)` y `out_valid = !rst && full`. Si está lleno y la salida no acepta, mantener el paquete; si la salida acepta, permitir reemplazarlo en el mismo flanco con una entrada aceptada. Si no llega reemplazo, quedar vacío. Reset vacía el registro y anula la muestra pendiente.

**Prueba de aceptación:** primera muestra un ciclo después de capturarla, flujo de varias muestras sin pausas, salida frenada con registro lleno, reemplazo simultáneo, último dato detenido y reset en ese estado. Verificar exactamente un dato entregado por cada dato capturado, salvo cancelación por reset.

### Contrato externo que cumplen los dos núcleos

Cada núcleo expone `clk`, `rst`, el enlace de entrada con `W_IN/F_IN` y el de salida con `W_OUT/F_OUT`. El núcleo produce `in_ready` y `out_valid`; los bloques externos producen `in_valid` y `out_ready`, respectivamente. Acepta cada muestra una vez, mantiene la salida hasta aceptación y respeta el mismo inicio/fin de trama y conteo. Su latencia y tasa de aceptación son propias y deben documentarse.

El filtro temporal puede calcular por muestra y el de frecuencia por bloques; ambos entregan muestras en el mismo orden lógico. La terminación de cada enlace es su propia aceptación: que el núcleo haya entregado su último dato al registro de salida no significa que el receptor externo ya lo haya aceptado. La cadena termina externamente con `out_valid && out_ready && out_last` en la salida común.


## Entregables y decisiones por cerrar

- [x] Reparto de cuatro módulos entre Enzo y Julián acordado, con revisión cruzada.
- [ ] Cerrar fuente de bits, mapeo, semilla, configuración de longitud y primera salida del generador.
- [ ] Cerrar `W_IN/F_IN`, `W_OUT/F_OUT`, `LEN_W/SEED_W`, nombres definitivos y representación I/Q.
- [ ] Cerrar flanco, tipo/polaridad de reset, anulación de datos pendientes y vuelta a operación.
- [ ] Cerrar marcador/longitud de trama, tramas vacías y preparación del historial entre tramas independientes.
- [ ] Cerrar capacidad, latencia e intervalo de inicio de generador, upsampler y salida; conexión directa o registrada en entrada.
- [ ] Registrar el contrato acordado en E03 y configuración consumida por código, con un cronograma con pausas.
- [ ] Julián: implementar generador QPSK y etapa de salida con sus testbenches.
- [ ] Enzo: implementar upsampler y adaptador/wrapper de entrada con sus testbenches.
- [ ] Completar revisión cruzada e integración en temporal y frecuencia.
- [ ] Registrar fuentes comunes y testbenches junto con las variantes RTL para que CI ejecute las pruebas; no contar un smoke sin RTL como validación de hardware.

## Criterios de aceptación

- Generador: conteo de símbolos exacto, secuencia reproducible con la fuente/semilla acordada, signos/mapeo correctos y mismo resultado pese a pausas; no avance por una transferencia no aceptada.
- Upsampler: S símbolos aceptados producen exactamente 2S muestras aceptadas en orden símbolo/cero; último cero incluido; marca de trama conservada bajo pausas; sin pérdida ni duplicación.
- Adaptador: valores, orden, formato y metadatos idénticos a ambos lados; pausas/reset según contrato; latencia declarada y comprobada.
- Salida: conservación del paquete mientras el receptor espera; reemplazo simultáneo cuando corresponda; orden y conteo exactos; ninguna entrega repetida al mantener `valid` alto.
- Reset durante operaciones y último dato detenido: cancelación/vaciado definidos, sin mezclar tramas. Cubrir tramas consecutivas y el tratamiento acordado de trama vacía.
- Integración: ambos núcleos consumen la misma secuencia de muestras. Para S símbolos y recorte sin cola, ambos producen 2S resultados por índice lógico aunque difieran ciclos/ráfagas. La correspondencia numérica usa el criterio externo acordado; cada núcleo resuelve su aritmética internamente.
- Evidencia reproducible: comando de testbench por módulo e integración, configuración/semilla, PASS/FAIL y diagnóstico. Ejecutar `make smoke` y `git diff --check` antes de los PR; los testbenches deben fallar cuando hay discrepancias.

## Orden de implementación y cierre

1. Cerrar contrato externo en E03 y documentar las decisiones todavía propuestas.
2. Julián prepara generador; Enzo prepara upsampler; revisar ambos y probar su conexión.
3. Enzo prepara entrada y Julián salida; probar pausas, reset y marca final en toda la cadena.
4. Cada uno integra los bloques en su propio núcleo y registra evidencia.
5. Cerrar con RTL compartido, revisión cruzada y pruebas de las dos integraciones; mantener los acuerdos en el contrato permanente y el Markdown temporal ya fue migrado a este contrato y a la issue #31.

Las salidas de una fuente no se conectan sin adaptación a dos receptores con diferentes `ready`: usar pruebas independientes con la misma secuencia o un distribuidor que registre la aceptación por rama. La finalización externa se reconoce en la aceptación de la última muestra de la salida común, no al terminar de generar símbolos.
