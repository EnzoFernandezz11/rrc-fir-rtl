# Contrato técnico compartido

**Estado:** borrador de etapa 0
**Fuente:** [consigna original](consigna-original.md) facilitada por el equipo el 2/10/2026
**Revisión conjunta A/B/C:** pendiente
**Regla:** este documento define el comportamiento esperado; [`config/project.json`](../config/project.json) contiene los valores que consumen los scripts. Modificar ambos en el mismo PR cuando cambie un parámetro.

Los acuerdos detallados se completan en [contratos de trabajo](contratos/README.md). Este documento reúne los requisitos y el estado de las decisiones; cada contrato detalla una interfaz o método para que A, B y C trabajen en paralelo.

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
| D01 | ¿Qué operaciones exactas componen el filtro en frecuencia? ¿Tamaño de bloque/FFT, convolución lineal o circular, overlap-add/save y latencia? | abierto | C | Pendiente. |
| D02 | ¿Cuáles son los 8 coeficientes exactos, su orden, fase de muestreo, escala y normalización? Roll-off y 2× solos no fijan una tabla única. | abierto | A | Pendiente. |
| D03 | ¿Cómo se codifican QPSK, I/Q, `valid`, reset y límites de bloque en la interfaz? | abierto | A/B/C | Pendiente. |
| D04 | ¿Qué anchos, punto binario, redondeo y saturación tendrá cada nodo? | abierto | A | Depende de barrido SQNR. |
| D05 | ¿Qué plataforma, biblioteca, reloj y constraints se usarán para comparar PPA? | abierto | B/C | Pendiente. |
| D06 | ¿Cómo se estimará potencia con los mismos estímulos y condiciones para las cuatro variantes? | abierto | A/B/C | Pendiente. |
| D07 | ¿Cuál es la definición de SQNR: referencia, muestras descartadas, tratamiento de I/Q y casos usados? | abierto | A | Pendiente. |
| D08 | ¿Qué arquitectura se elige para cada variante optimizada y qué eje PPA intenta mejorar? | abierto | B/C | Después de las seriales. |

## 3. Coeficientes y señales

| Parámetro | Valor | Estado/fuente |
|---|---|---|
| Modulación | QPSK | Consigna. |
| Sobremuestreo | 2 muestras/símbolo | Consigna. |
| Número de coeficientes | 8 | Consigna. |
| Roll-off | 0,5 | Consigna. |
| Coeficientes `h[0]…h[7]` | Por definir | D02. |
| Normalización de energía/ganancia | Por definir | D02. |
| Mapeo de símbolos y amplitud I/Q | Por definir | D03. |

Al cerrar D02, pegar aquí la tabla de coeficientes **con precisión suficiente para reproducirla**, fórmula o script que la generó, y dos ejemplos de salida (impulso y secuencia corta). Los archivos `vectors/` deberán derivarse de la misma configuración.

## 4. Método en frecuencia

| Aspecto | Decisión |
|---|---|
| Transformada y tamaño | Por definir. |
| Organización de bloques | Por definir. |
| Solapamiento/descarte | Por definir. |
| Orden y escala de FFT/IFFT | Por definir. |
| Alineación con salida temporal | Por definir. |
| Latencia y throughput | Por definir. |

Antes de C01/C02 debe haber un modelo flotante que muestre cómo se corresponden las salidas temporal y en frecuencia para impulso, QPSK y límites de bloque. Si el docente espera otra definición, registrar la respuesta y cambiar los modelos antes del RTL.

## 5. Contrato de punto fijo

| Señal/nodo | Signo | Bits totales | Bits fraccionarios | Redondeo | Saturación/overflow |
|---|---|---:|---:|---|---|
| Entrada I/Q | Por definir | — | — | — | — |
| Coeficientes | Por definir | — | — | — | — |
| Producto | Por definir | — | — | — | — |
| Acumulador | Por definir | — | — | — | — |
| Salida I/Q | Por definir | — | — | — | — |

El barrido de A04 debe fijar estos valores con evidencia SQNR ≥ 40 dB y registrar casos de saturación. El SQNR no se reportará sin indicar señal de referencia, intervalo de muestras y fórmula exacta.

## 6. Interfaz RTL y verificación

| Puerto o regla | Definición |
|---|---|
| Reloj y reset | Por definir. |
| Entrada I/Q y formato | Por definir. |
| Entrada/salida `valid` o handshake | Por definir. |
| Inicio/fin de bloque | Por definir. |
| Orden de salida y latencia | Por definir para cada arquitectura. |
| Casos mínimos | Impulso, ceros, QPSK determinista, extremos numéricos y límites de bloque. |

El testbench de cada variante debe comparar por **índice de muestra válido** con su modelo fijo. Las diferencias entre dominios pueden necesitar tolerancia numérica por distintos puntos de redondeo; registrar la tolerancia, no ocultar discrepancias. El banco común debe informar muestra, I/Q, esperado y obtenido al fallar.

## 7. Comparación PPA

| Métrica | Condición de comparación |
|---|---|
| Área | Misma tecnología, biblioteca o FPGA y flujo de síntesis. Reportar celdas/recursos y fuente del log. |
| Performance | Reloj objetivo, Fmax/timing **medido tras implementación**, latencia en ciclos y throughput en muestras/s. |
| Potencia | Método, frecuencia, actividad de entrada y herramienta por definir en D06. |
| Precisión | Mismo conjunto de vectores y definición de SQNR. |

Yosys sin place-and-route permite comparar recursos de síntesis; no prueba por sí solo que un diseño alcance 100 o 10 MHz. La comparación final debe distinguir datos medidos de estimaciones.

## 8. Cambios y consultas al docente

| Fecha | ID | Pregunta o cambio | Respuesta/fuente | Efecto en modelo, RTL y pruebas | PR |
|---|---|---|---|---|---|
| 2026-10-02 | D01–D07 | Primera lista de decisiones abiertas. | Consigna formal. | Bloquean el cierre del contrato técnico. | — |

E00–E03 se cierran cuando las decisiones relevantes tienen respuesta, fuente y revisión de los tres. Las nuevas decisiones se agregan aquí antes de incorporarlas a `config/project.json`.
