# Contrato: señales, coeficientes y punto fijo

**Estado:** Abierto
**Prepara:** @andres332271
**Revisan:** @moreyrajulian y @EnzoFernandezz11
**Issues:** E02, A01, A04, A05
**Fuente:** [consigna original](../consigna-original.md) y decisiones D02–D04 del [contrato técnico](../contrato-tecnico.md).

## Confirmado por la consigna

QPSK, filtro complejo con 8 coeficientes RRCOS, roll-off 0,5 y sobremuestreo 2×. La tabla exacta de coeficientes, amplitud de QPSK, normalización y formatos todavía no está fijada.

## Decisiones para trabajar en paralelo

| Punto | Valor acordado | Fuente/ejemplo | Estado |
|---|---|---|---|
| Mapeo bits → símbolos QPSK y amplitud I/Q | Por definir | — | Abierto |
| Inserción de ceros/interpolación para 2× | Por definir | — | Abierto |
| Fórmula y fase de muestreo RRCOS | Por definir | — | Abierto |
| Tabla `h[0]…h[7]` y orden de taps | Por definir | — | Abierto |
| Escala de coeficientes y ganancia total | Por definir | — | Abierto |
| Formato de entrada, producto, acumulador y salida | Por definir | — | Abierto |
| Redondeo y saturación en cada corte | Por definir | — | Abierto |

## Tabla de formatos a completar tras el barrido SQNR

| Nodo | Con signo | Bits totales | Bits fraccionarios | Rango | Política al reducir bits |
|---|---|---:|---:|---|---|
| Entrada I/Q | — | — | — | — | — |
| Coeficientes | — | — | — | — | — |
| Producto | — | — | — | — | — |
| Acumulador | — | — | — | — | — |
| Salida I/Q | — | — | — | — | — |

## Ejemplos obligatorios antes de aprobar

1. Una secuencia QPSK breve con los símbolos complejos y las muestras 2× exactas.
2. Tabla de los ocho coeficientes con precisión suficiente para reproducirla, la fórmula o script que la genera y la respuesta al impulso con índice de muestra.
3. Un ejemplo de multiplicación/acumulación en punto fijo que muestre signo, redondeo y saturación.
4. Archivo de configuración/semilla que regenere los vectores, y evidencia SQNR ≥ 40 dB con la definición acordada.

Al aprobar, copiar **solo los valores consumidos por código** a `config/project.json`. El modelo, RTL y testbench deben leer o derivar el mismo orden y escala.
