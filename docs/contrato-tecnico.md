# Contrato técnico compartido

**Estado:** borrador de etapa 0
**Fuente:** [consigna original](consigna-original.md) facilitada por el equipo el 2/10/2026
**Revisión conjunta de @andres332271, @moreyrajulian y @EnzoFernandezz11:** pendiente
**Regla:** este documento define el comportamiento esperado; [`config/project.json`](../config/project.json) contiene los valores que consumen los scripts. Modificar ambos en el mismo PR cuando cambie un parámetro.

Los acuerdos detallados se completan en [contratos de trabajo](contratos/README.md). Este documento reúne los requisitos y el estado de las decisiones; cada contrato detalla una interfaz o método para que @andres332271, @moreyrajulian y @EnzoFernandezz11 trabajen en paralelo.

## 1. Requisitos confirmados

| Tema | Requisito |
|---|---|
| Entrada | Símbolos QPSK; datos complejos I/Q. |
| Filtros | Uno complejo en tiempo y otro en frecuencia, implementados por separado. |
| Coeficientes | 8 de un RRCOS, roll-off 50 %, sobremuestreo 2×. |
| Secuencia | Modelo Python flotante → modelo de punto fijo y barrido de bits → versiones seriales y vector matching → optimización PPA. |
| Precisión | SQNR no inferior a 40 dB. |
| Optimizaciones posibles | Paralela/unfolded, pipeline, sistólica, folded o combinación. |
| Metas de reloj | Versiones rápidas: 100 MHz; lentas: 10 MHz. |
| Entrega | Filminas que contrasten resultados y aprendizajes; Gantt con tareas y distribución; presentación en fecha acordada antes de terminar 2026. |

La implementación temporal con 8 taps se tratará como FIR complejo: `y[n] = Σ(k=0..7) h[k]·x[n−k]`. El filtro en frecuencia debe concretarse en D01 antes de fijar RTL: la consigna no define tamaño de bloque, transformada ni tratamiento del solapamiento. Esta ecuación no autoriza a asumir que cualquier producto de FFT por coeficientes es equivalente a convolución lineal.

## 2. Registro de decisiones de etapa 0

Estados permitidos: **abierto**, **provisional**, **confirmado por consigna**, **confirmado por docente**, **acordado por equipo**. Una decisión provisional puede servir para experimentar, pero no se presenta como requisito confirmado.

| ID | Tema y pregunta concreta | Estado | Responsable | Evidencia o respuesta |
|---|---|---|---|---|
| D01 | ¿Qué operaciones exactas componen el filtro en frecuencia? ¿Tamaño de bloque/FFT, convolución lineal o circular, overlap-add/save y latencia? | abierto | @EnzoFernandezz11 | Pendiente. |
| D02 | ¿Cuáles son los 8 coeficientes exactos, su orden, fase de muestreo, escala y normalización? Roll-off y 2× solos no fijan una tabla única. | abierto | @andres332271 | Pendiente. |
| D03 | ¿Cómo se codifican QPSK, I/Q, `valid`, reset y límites de bloque en la interfaz? | abierto | @andres332271, @moreyrajulian y @EnzoFernandezz11 | Pendiente. |
| D04 | ¿Qué anchos, punto binario, redondeo y saturación tendrá cada nodo? | abierto | @andres332271 | Depende de barrido SQNR. |
| D05 | ¿Qué plataforma, biblioteca, reloj y constraints se usarán para comparar PPA? | abierto | @moreyrajulian y @EnzoFernandezz11 | Pendiente. |
| D06 | ¿Cómo se estimará potencia con los mismos estímulos y condiciones para las cuatro variantes? | abierto | @andres332271, @moreyrajulian y @EnzoFernandezz11 | Pendiente. |
| D07 | ¿Cuál es la definición de SQNR: referencia, muestras descartadas, tratamiento de I/Q y casos usados? | abierto | @andres332271 | Pendiente. |
| D08 | ¿Qué arquitectura se elige para cada variante optimizada y qué eje PPA intenta mejorar? | abierto | @moreyrajulian y @EnzoFernandezz11 | Después de las seriales. |

## 3. Detalle por tema

Las tablas de cada tema viven en un solo lugar, el contrato de trabajo correspondiente. Este documento solo registra el estado de la decisión (sección 2) y los cambios (sección 4).

| Tema | Decisiones | Contrato |
|---|---|---|
| Coeficientes, QPSK, I/Q y punto fijo | D02, D03, D04 | [Señales y formatos](contratos/senales-y-formatos.md) |
| Filtro en frecuencia | D01 | [Método en frecuencia](contratos/frecuencia.md) |
| Puertos, `valid`, reset y latencia | D03 | [Interfaz RTL](contratos/interfaz-rtl.md) |
| Vector matching, SQNR y PPA | D05, D06, D07 | [Verificación y PPA](contratos/verificacion-y-ppa.md) |
| Arquitecturas optimizadas | D08 | Nota en el PR de B03/C03 y fila D08 de la sección 2. |

## 4. Cambios y consultas al docente

| Fecha | ID | Pregunta o cambio | Respuesta/fuente | Efecto en modelo, RTL y pruebas | PR |
|---|---|---|---|---|---|
| 2026-10-02 | D01–D07 | Primera lista de decisiones abiertas. | Consigna formal. | Bloquean el cierre del contrato técnico. | — |

E00–E03 se cierran cuando las decisiones relevantes tienen respuesta, fuente y revisión de los tres. Las nuevas decisiones se agregan aquí antes de incorporarlas a `config/project.json`.
