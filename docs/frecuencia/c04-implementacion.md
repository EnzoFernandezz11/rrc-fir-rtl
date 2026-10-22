# C04 — Contrato de implementación y aceptación

Implementación de [C03](c03-optimizacion.md) en `rtl/frequency_optimized/`.
Issue: [C04 #19](https://github.com/EnzoFernandezz11/rrc-fir-rtl/issues/19).
Top y target: `fir_frequency_optimized` / `frequency_optimized`. La referencia
numérica sigue siendo `model.fixed_point` y las columnas `yf` de A05.

## Interfaces y fronteras de registro

Entrada compleja signed 2/F0, trabajo 12/F5, constantes 10/F8 y salida 9/F7.
Interfaz externa `clk`, `rst` síncrono alto y enlaces `in_*` / `out_*`
con I/Q, valid, ready y last. Buses vectoriales aplanados: componente k en
`[k*W +: W]`. No se modifica la cuantización ni se agrega saturación.

| Módulo | I/O | Aceptación |
|---|---|---|
| `frequency_csd_mul` | Operando signed 12/13, constante de elaboración; producto 22/23 | Igualdad exhaustiva con multiplicación entera; red equilibrada sin multiplicador variable. |
| `frequency_complex_const` | I/Q 12, constantes C_I/C_Q, valid; resultado 12 y valid | Especializaciones cero, real puro, ±j, componentes iguales y general; corte opcional dentro del producto; signos y guardias exactos. |
| `frequency_butterfly` | A/B complejos 12, valid; suma/diferencia 12 y valid | A y bypass alineados; sumas de 13 bits; captura final propiedad de la etapa. |
| `frequency_fft16` | Vector natural 16×12 I/Q, valid; vector natural y valid; INVERSE estático | FFT e IFFT separadas; bit reversal fijo; etapas 1+1+2+2 ciclos contando destino. |
| `frequency_spectral16` | X 16×12 I/Q, valid; Y y valid | 16 posiciones H fijas; dos ciclos contando captura Y; bin cero alineado. |
| `frequency_output_scale` | Ocho complejos útiles 12; ocho complejos 9 | (+2) >>> 2 con guardia, un ciclo contando captura en buffer. |
| `fir_frequency_optimized_control` | Handshakes y finalizaciones; habilitaciones, índices y reservas | FIFO, reserva exclusiva, liberación tras captura, reset de toda validez. |
| `fir_frequency_optimized` | Interfaz pública | Historial, ventanas, bancos y datapaths; equivalencia exacta e II de bloque 8. |

FFT registra E1/E2/E3 y los productos de E3/E4. Su salida E4 es combinacional
para escribir directamente el banco X en el sexto flanco de captura. Espectral
registra productos y escribe directamente Y en el segundo flanco. IFFT termina
en el registro de ocho resultados útiles; la conversión escribe el buffer de
salida al flanco siguiente. Los bancos no agregan registros intermedios.
Los bancos externos capturan únicamente cuando `out_valid` está activo.

Cada lanzamiento reserva su destino y registra la petición; la primera captura
ocurre al flanco siguiente. Datos y token (destino, p de 4 bits, last) avanzan
juntos. Desde lanzamiento FFT: X completo en 6, lanzamiento espectral en 7,
Y completo en 9, lanzamiento IFFT en 10, útiles en 16, salida completa en 17
y primeras transferencias en 18…25. La ventana se completa antes del lanzamiento.

## Control y almacenamiento

Dos ventanas de 16 complejos 2/F0; historial independiente de ocho; dos bancos
X y dos Y de 16 complejos 12/F5; dos buffers de ocho salidas 9/F7.
Estados libre/reservado/completo; orden FIFO sin alternar ciegamente.
Origen liberado en la primera captura del consumidor. No hay pausas internas
en operaciones iniciadas; falta de espacio frena lanzamientos y luego entrada.
No se necesita reutilizar el mismo banco en su flanco de liberación.

Historial avanza solo al aceptar muestras. Captura en orden natural, copia de
historial paralela, bloques parciales rellenados con cero y p entre 1 y 8.
No hay burbuja entre ventanas completas ni entre buffers completos de salida.
Después de in_last se detiene entrada hasta aceptar out_last; la trama siguiente
empieza con historial cero. Salida retenida estable. Reset cancela toda reserva,
validez y trama parcial. No hay transferencias durante reset.

## Entregas pequeñas y responsables

El coordinador fija interfaces, revisa entregas, conecta el top y ejecuta la
regresión final. Hasta tres trabajadores simultáneos; un único escritor por
archivo compartido. Cada tarea entrega código y su prueba antes de avanzar.

1. Aritmética: CSD exhaustivo; luego producto complejo y extremos.
2. Aritmética: mariposa y después FFT/IFFT con checkpoints del modelo.
3. Aritmética: espectral y conversión, con verificación de latencia.
4. Control: captura/historial/ventanas; luego reservas y emisión con pipelines.
5. Verificación: banco integrado A05/A04; después estrés, reset y rendimiento.
6. Coordinador: integración, registro CI/síntesis y benchmark/paquete PPA.

## Pruebas y cierre

- Unitarias: todas las constantes/entradas CSD; productos y mariposas con signos,
  extremos y empates; detección de overflow; etapas FFT/IFFT contra modelo.
- Integración: A05 y vectores extendidos existentes, longitudes 0…40, impulsos,
  extremos y cinco semillas de SQNR ≥40 dB; comparación exacta por handshake.
- Protocolo: burbujas, backpressure prolongado, bancos ocupados, tramas sin reset,
  reset durante captura/cálculo/espera/emisión; sin pérdida, duplicación o mezcla.
- Rendimiento: al menos 2048 muestras continuas; aceptación/emisión sin burbujas
  en régimen, II_bloque=8; medir L según el contrato y distinguir llenado/vaciado.
- Ejecutar `make smoke` y `make full`; síntesis sin latches ni `$mul` en CSD.
  Sintetizar temprano aritmética/E4 y después el conjunto.
- Preparar paquete Vivado externo de 10 ns con fuentes, vectores, versiones y
  hashes. Medir setup/hold, recursos, simulación SDF y potencia con SAIF.
  Throughput sostenido y throughput de la ventana de actividad se reportan aparte.

La evidencia física queda pendiente de ejecutar Vivado externo. C04 no se cierra
sin esa evidencia (o decisión escrita revisada admitida por la issue) y A06
resuelta. No se presume cierre de timing por pasar simulación o síntesis Yosys.

## Evidencia funcional de la implementación

El banco integrado ejecuta 837 tramas: cada una de las 369 tramas extendidas
A04 se prueba con y sin pausas, además de los archivos A05, QPSK, una trama de
4096 muestras (512 bloques), backpressure prolongado y reset barrido a través
del pipeline. Las salidas se comparan por handshake; las pruebas de recuperación
usan una trama de ceros para detectar historial o resultados anteriores.

La simulación integrada midió L=26 ciclos para bloques completos, aceptación y
emisión de una muestra por ciclo en régimen e II_bloque=8. Las cinco semillas
QPSK conservan SQNR mínima de 42,959 dB por igualdad exacta con el modelo fijo.
Las tramas de menos de ocho muestras tienen latencia menor por su cierre parcial;
no se les impone el calendario continuo de bloques completos.

Las unitarias comprueban CSD exhaustivo de 12/13 bits, productos complejos y
mariposas con overflow deliberado, ocho checkpoints FFT/IFFT sobre 256 ventanas,
alineación espectral con reset y escala exhaustiva en el rango representable.
Los errores de formato A05 se ejercitan sobre el lector real de ambas variantes.

Comandos reproducibles:

```sh
make verify
python3 -m unittest tests.test_frequency_arithmetic tests.test_frequency_transform tests.test_frequency_spectral tests.test_frequency_optimized -v
python3 scripts/ppa.py package --target frequency_optimized
```

`package` vuelve a ejecutar smoke y conserva sus logs junto al benchmark y al
mapeo. Los resultados se registran en [`reports/ppa/frequency.md`](../../reports/ppa/frequency.md).
La medición local actual usa SKY130 HD; sus áreas son áreas de celdas y no
incluyen STA, ruteo ni potencia. El período de 10 ns citado por el benchmark es
solo de simulación. Para el flujo y sus límites, ver la [guía PPA](ppa.md).

## Evidencia histórica de mapeo XC7 y limitaciones

La corrida histórica de Yosys XC7 produjo 7493 LUT de lógica, 5140 FF, 1750
CARRY4, 168 RAM32M, 0 DSP48E1 y 0 BRAM. RAM32M es memoria distribuida, contada por separado de las
LUT1…LUT6; no debe omitirse al comparar área. Yosys infiere bancos anchos de dos
palabras a partir de los arrays de registros: conserva accesos vectoriales y la
semántica de reservas. No se reemplazó el datapath por una RAM serial de pocos
puertos. El presupuesto nominal de 7984 bits de C03 no es un conteo físico de FF.

El benchmark de simulación local de 2048 muestras midió 2074 ciclos activos:
98,746 millones de muestras/s efectivos al período simulado de 10 ns, frente a
100 millones/s sostenidos según ese reloj simulado. Estas cifras no validan
operación física a 100 MHz. El área citada arriba es mapeo lógico XC7 histórico,
no una medida SKY130; timing físico, ruteo y potencia requieren evidencia del
flujo correspondiente.
