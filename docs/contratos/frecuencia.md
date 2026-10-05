# Contrato: filtro en el dominio de la frecuencia

**Estado:** Abierto
**Prepara:** @EnzoFernandezz11
**Revisan:** @andres332271 y @moreyrajulian
**Issues:** E01, A03, C01, C02
**Fuente:** [consigna original](../consigna-original.md), decisión D01 del [contrato técnico](../contrato-tecnico.md).

La consigna nombra un filtro complejo en frecuencia pero no especifica una arquitectura de bloques. No escribir RTL definitivo hasta dejar respondidos estos puntos o registrar una hipótesis provisional que luego pueda cambiarse.

| Punto | Decisión | Evidencia |
|---|---|---|
| Transformada elegida y longitud `N` | Por definir | — |
| Relación entre 8 taps y respuesta en frecuencia | Por definir | — |
| Convolución lineal o circular | Por definir | — |
| Método de solapamiento (si aplica) | Por definir | — |
| Orden, escala y cuantización FFT/IFFT | Por definir | — |
| Entrada/salida de bloques parciales | Por definir | — |
| Latencia y throughput serial esperados | Por definir | — |

## Prueba mínima para cerrar el contrato

El modelo Python flotante temporal y el de frecuencia deben producir salidas alineadas para impulso, ceros, QPSK y secuencias que crucen límites de bloque, con una tolerancia numérica declarada. Registrar muestras descartadas, retardo y cualquier diferencia intencional. Si el objetivo docente es distinto de esta equivalencia, registrar la respuesta antes de aprobar.

## Pregunta al docente

> Para el filtro de 8 coeficientes RRCOS en frecuencia, ¿espera una implementación por bloques de la misma convolución del filtro temporal? De ser así, ¿hay tamaño de transformada, método de solapamiento o latencia exigidos?
