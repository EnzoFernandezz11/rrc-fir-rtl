# Modelos Python

A implementará aquí QPSK, generación de coeficientes, filtros flotantes y versiones de punto fijo según los [contratos](../docs/contrato-tecnico.md#3-detalle-por-tema). Cada modelo debe declarar formato, orden de muestras y latencia, y exportar vectores deterministas. Las pruebas van en `tests/`.

- `qpsk_rrc.py` (A01): símbolos QPSK ±1±1j con semilla, sobremuestreo 2× por inserción de ceros y 8 coeficientes RRCOS en la grilla ±0,25…±1,75 Ts. `python3 model/qpsk_rrc.py --seed 1` imprime la tabla de coeficientes y una secuencia de ejemplo. La normalización a energía unitaria es provisional hasta E02.
- `fixed_point.py` (A04): modelos bit-true `fir_time_fxp` y `fir_frequency_fxp` (motor de C01), con los formatos de `config/project.json`; enteros con los bits fraccionarios de cada nodo, redondeo mitad hacia arriba y `OverflowError` en vez de saturar. `python3 -m model.fixed_point` imprime el barrido SQNR, la cota del banco `work` y los anchos. Ver [formatos](../docs/contratos/senales-y-formatos.md#formatos-de-punto-fijo-a04).
- `vectors.py` (A05): `python3 -m model.vectors` regenera [vectors/](../vectors/README.md) con entradas y salidas esperadas de ambas ramas; `read()` es el lector de referencia.
- `fir_time.py` (A02): FIR temporal flotante `fir_time(x, h)`, con historial inicial cero, una salida por muestra y sin cola, la misma convención que `frequency_filter` de E01. `python3 -m model.fir_time --seed 1` escribe en `build/a02/` un CSV por caso (impulso, ceros y QPSK 2×) con columnas `n,x_i,x_q,y_i,y_q`. El formato definitivo de vectores lo fija A05.
