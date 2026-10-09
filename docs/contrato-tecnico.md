# Contrato técnico compartido

**Estado:** borrador de etapa 0
**Fuente:** [consigna vigente](consigna-actualizada.md), confirmada por Enzo el 7/10/2026
**Revisión conjunta de @andres332271, @moreyrajulian y @EnzoFernandezz11:** pendiente
**Regla:** este documento define el comportamiento esperado; [`config/project.json`](../config/project.json) contiene los valores que consumen los scripts. Modificar ambos en el mismo PR cuando cambie un parámetro.

Este documento reúne los requisitos y el estado de las decisiones. Los acuerdos detallados están en los contratos de trabajo de la [sección 3](#3-detalle-por-tema); cada uno detalla una interfaz o método para que @andres332271, @moreyrajulian y @EnzoFernandezz11 trabajen en paralelo.

## 1. Requisitos confirmados por la consigna vigente

| Tema | Requisito |
|---|---|
| Entrada | Símbolos QPSK con componentes ±1; datos complejos I/Q. |
| Filtro temporal | FIR RRCOS de 8 taps, roll-off 0,5. |
| Filtro en frecuencia | Procesamiento por bloques con superposición del 50 %, basado en FFT. |
| Correspondencia | Verificar resultados entre ambas implementaciones con los mismos coeficientes y entradas. |
| Comparación numérica | Flotante frente a punto fijo con distintos conjuntos de datos. |
| Implementación | Completar interfaz serie y luego implementación paralela mediante pipeline, sistólica, folded u otra equivalente. |
| Frecuencia optimizada | Mayor paralelización posible de FFT, multiplicación espectral e IFFT. |
| Documentación | Diagrama de bloques completo, descripción de etapas y Gantt con aportes individuales. |
| Defensa | En la fecha acordada. |

La referencia temporal es `y[n] = Σ(k=0..7) h[k]·x[n−k]`. La propuesta D01 implementa esa misma convolución mediante overlap-save FFT16, con ocho muestras de historial y ocho nuevas. La consigna fija FFT y superposición del 50 %; el tamaño 16 y el método overlap-save son elecciones de implementación justificadas en el [contrato de frecuencia](contratos/frecuencia.md).

### Mínimos adicionales confirmados por Enzo el 7/10/2026

| Magnitud | Requisito mínimo |
|---|---|
| SQNR | ≥ 40 dB. |
| Frecuencia de reloj, variantes lentas | ≥ 10 MHz. |
| Frecuencia de reloj, variantes rápidas | ≥ 100 MHz. |

Estos mínimos complementan el texto de la consigna y se registran con la aclaración de Enzo como fuente. La frecuencia corresponde al reloj; el throughput se mide por separado según los ciclos por muestra y las pausas.

### Decisión de upsampling y planificación

Enzo confirmó el **upsampling 2× el 7/10/2026** como decisión de diseño para ambas cadenas: un **upsampler** separado inserta un cero complejo después de cada símbolo, `x[2m]=a[m]`, `x[2m+1]=0`. El antecedente indicado por Enzo es el upsampling utilizado a la entrada en el curso de Óptica. La consigna no fija el factor; esta elección tiene como fuente la confirmación de Enzo y deja de ser una propuesta pendiente de consulta. La revisión conjunta del contrato sigue pendiente, sin atribuir aprobación docente ni del equipo a esta confirmación.

En `config/project.json`, `confirmed` contiene los parámetros de la consigna y los mínimos adicionales confirmados por Enzo; `decisions.samples_per_symbol` registra valor 2, estado `confirmed_by_enzo`, fecha y fuente. La fecha planificada 30/10/2026 es una meta heredada del proyecto, ausente del texto vigente. La tabla exacta de coeficientes sigue en E02: elegir 2× no determina por sí solo fase ni normalización.

## 2. Registro de decisiones de etapa 0

Estados permitidos: **abierto**, **propuesto**, **provisional**, **confirmado por consigna**, **confirmado por Enzo**, **confirmado por docente**, **acordado por equipo**. Una decisión provisional puede servir para experimentar, pero no se presenta como requisito confirmado.

| ID | Tema y pregunta concreta | Estado | Responsable | Evidencia o respuesta |
|---|---|---|---|---|
| D01 | ¿Qué operaciones exactas componen el filtro en frecuencia? ¿Tamaño de bloque/FFT, convolución lineal o circular, overlap-add/save y latencia? | propuesto | @EnzoFernandezz11 | [Contrato de frecuencia](contratos/frecuencia.md): overlap-save FFT16/IFFT16, historial y avance de ocho, salidas causales sin cola y latencia estructural. Evidencia en `tests/test_frequency_overlap_contract.py`; PR #28. |
| D02 | ¿Cuáles son los 8 coeficientes exactos, su orden, fase de muestreo, escala y normalización? Roll-off y 2× solos no fijan una tabla única. | provisional | @andres332271 | Propuesta E02 en [señales y formatos](contratos/senales-y-formatos.md): grilla ±0,25…±1,75 Ts, energía unitaria. Pasa a acordado por equipo al integrar el PR con la revisión de los tres. |
| D03 | ¿Cómo se codifican QPSK, I/Q, `valid`, reset y límites de bloque en la interfaz? | propuesto | @andres332271, @moreyrajulian y @EnzoFernandezz11 | E02 propone el mapeo QPSK y la entrada I/Q de 2 bits. E03 propone en la [interfaz RTL](contratos/interfaz-rtl.md) `valid/ready` con `last`, I/Q `signed` en puertos separados y `rst` síncrono activo alto. |
| D04 | ¿Qué anchos, punto binario, redondeo y saturación tendrá cada nodo? | abierto | @andres332271 | Depende de barrido SQNR. |
| D05 | ¿Qué plataforma, biblioteca, reloj y constraints se usarán para comparar PPA? | propuesto | @moreyrajulian y @EnzoFernandezz11 | E03 propone Vivado out-of-context sobre Artix-7, con relojes de 100 y 10 MHz en `constraints/`. Ver [verificación y PPA](contratos/verificacion-y-ppa.md#ppa). |
| D06 | ¿Cómo se estimará potencia con los mismos estímulos y condiciones para las cuatro variantes? | propuesto | @andres332271, @moreyrajulian y @EnzoFernandezz11 | E03 propone `report_power` de Vivado con actividad SAIF de la simulación del vector QPSK de A05, y energía por muestra. Ver [verificación y PPA](contratos/verificacion-y-ppa.md#ppa). |
| D07 | ¿Cuál es la definición de SQNR: referencia, muestras descartadas, tratamiento de I/Q y casos usados? | abierto | @andres332271 | Pendiente. |
| D08 | ¿Qué arquitectura se elige para cada variante optimizada y qué eje PPA intenta mejorar? | abierto | @moreyrajulian y @EnzoFernandezz11 | Después de las seriales. |

## 3. Detalle por tema

Las tablas de cada tema viven en un solo lugar, el contrato de trabajo correspondiente. Este documento solo registra el estado de la decisión (sección 2) y los cambios (sección 4).

| Tema | Decisiones | Contrato | Responsables |
|---|---|---|---|
| Coeficientes, QPSK, I/Q y punto fijo | D02, D03, D04 | [Señales y formatos](contratos/senales-y-formatos.md) | @andres332271 prepara; @moreyrajulian y @EnzoFernandezz11 revisan antes de tomar vectores como referencia. |
| Filtro en frecuencia | D01 | [Método en frecuencia](contratos/frecuencia.md) | @EnzoFernandezz11 propone; @andres332271 valida contra una referencia directa independiente y @moreyrajulian revisa la comparación. |
| Puertos, `valid`, reset y latencia | D03 | [Interfaz RTL](contratos/interfaz-rtl.md) | @moreyrajulian y @EnzoFernandezz11 acuerdan puertos y ciclos; @andres332271 valida que el banco común puede usarlos. |
| Vector matching, SQNR y PPA | D05, D06, D07 | [Verificación y PPA](contratos/verificacion-y-ppa.md) | @andres332271 prepara métricas y vectores; @moreyrajulian y @EnzoFernandezz11 validan que se ejecutan igual en sus variantes. |
| Arquitecturas optimizadas | D08 | Nota en el PR de B03/C03 y fila D08 de la sección 2. | @moreyrajulian y @EnzoFernandezz11. |

Cada contrato pasa por **Abierto → Propuesto → Aprobado por los tres**, y no se aprueba sin evidencia enlazada (respuesta del docente, ecuación, ejemplo numérico o prueba). Para cambiar un contrato aprobado: abrir issue o PR, explicar el impacto y actualizar `config/project.json`, modelos, vectores y RTL afectados en el mismo cambio o en PR dependientes declarados.

## 4. Cambios y consultas al docente

| Fecha | ID | Pregunta o cambio | Respuesta/fuente | Efecto en modelo, RTL y pruebas | PR |
|---|---|---|---|---|---|
| 2026-10-02 | D01–D07 | Primera lista de decisiones abiertas. | Registro histórico del proyecto. | Decisiones a resolver en E00–E03. | — |
| 2026-10-07 | D01 | Actualizar correspondencia FIR temporal/frecuencia y registrar propuesta FFT16. | Consigna vigente y corrección del review. | Ambas ramas comparten taps, entradas e índices; A04 fija tolerancia de punto fijo. | #28 |
| 2026-10-07 | D05, D07 | Precisar mínimos de SQNR y reloj. | Aclaración de Enzo: al menos 40 dB, 10 MHz en lentas y 100 MHz en rápidas. | A04 y RTL/PPA deben demostrar esos mínimos con las condiciones de medición acordadas. | #28 |
| 2026-10-07 | D02 | ¿Se mantiene sobremuestreo 2×? | Propuesta heredada; consulta docente por realizar. | Conservar 2× provisionalmente en modelos y ejemplos; fijar una tabla común en E02. | #28 |
| 2026-10-07 | D02, D03 | Enzo confirma upsampling 2× y el nombre upsampler. | Confirmación en conversación; antecedente del curso de Óptica. Sustituye la propuesta de la fila anterior. | Upsampler separado en ambas cadenas; S símbolos → 2S muestras. Configuración, modelos, pruebas y documentos usan la misma decisión y terminología. | — |
| 2026-10-07 | D02, D03 | Propuesta de coeficientes, normalización, mapeo QPSK y entrada I/Q. | E02. | Modelos A02/A03 y RTL B/C usan `decisions.coefficients`; la revisión conjunta sigue pendiente. | #33 |
| 2026-10-09 | D03, D05, D06 | Propuesta de interfaz RTL, plataforma PPA y método de potencia. | E03; la herramienta es Vivado porque @moreyrajulian la tiene disponible. | B01/C01 cumplen la interfaz; reemplaza el `rst_n` asíncrono elegido localmente en C01. Las cifras PPA salen de Vivado; la CI sigue con Yosys. | — |

E00–E03 se cierran cuando las decisiones relevantes tienen respuesta, fuente y revisión de los tres. Las nuevas decisiones se agregan aquí antes de incorporarlas a `config/project.json`.

## 5. Reparto RTL común

Enzo confirmó el 7/10/2026 que Julián aceptó inicialmente el reparto de generación y entrada/salida RTL. El [cierre posterior de R01 / #31](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/31) reemplazó esos bloques comunes por vectores Python inyectados directamente en cada núcleo. E03 propuso `valid/ready`, `last` y `rst` síncrono activo alto; los anchos de salida y formatos internos siguen pendientes de A04. Los núcleos y sus memorias/operadores se diseñan por separado.
