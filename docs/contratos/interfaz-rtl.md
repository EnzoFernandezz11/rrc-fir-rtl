# Contrato: interfaz RTL y temporización

**Estado:** Abierto
**Preparan:** B y C
**Revisa:** A
**Issues:** E03, B01, C01, A06

Ambos filtros deben exponer una interfaz comparable aunque sus latencias y tasas de aceptación difieran. Ningún puerto es definitivo hasta revisión A/B/C.

| Elemento | Definición a aprobar | Motivo |
|---|---|---|
| `clk` y polaridad/tipo de reset | Por definir | Reproducir inicio y vaciado de estados. |
| Ancho y signo de I/Q de entrada/salida | Por definir | Evitar conversiones ocultas en testbench. |
| Aceptación de entrada (`valid/ready` u otra) | Por definir | Una versión serial puede no aceptar una muestra por ciclo. |
| Validez de salida y backpressure | Por definir | Asociar cada salida a su muestra. |
| Inicio/fin de bloque en frecuencia | Por definir | Alinear bloques y solapamiento. |
| Orden de I/Q y primera muestra válida | Por definir | Vector matching sin desplazamientos arbitrarios. |
| Comportamiento ante reset y burbujas | Por definir | Pruebas de protocolo. |
| Latencia en ciclos/throughput por variante | Por medir | Comparación PPA. |

## Ejemplo de secuencia a documentar

Al aprobar, agregar una tabla ciclo a ciclo que muestre reset, primera muestra aceptada, burbujas y primera salida válida para temporal serial y frecuencia serial. La interfaz puede diferir internamente; el adaptador o banco común debe saber cuándo comparar cada índice de muestra.

## Revisión

- [ ] A puede escribir un testbench común sin conocer la FSM interna.
- [ ] B y C confirman que sus arquitecturas pueden cumplir la interfaz.
- [ ] El contrato precisa qué ocurre si llega una entrada mientras el diseño no está listo.
