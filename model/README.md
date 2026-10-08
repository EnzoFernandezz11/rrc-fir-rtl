# Modelos Python

A implementará aquí QPSK, generación de coeficientes, filtros flotantes y versiones de punto fijo según los [contratos](../docs/contratos/README.md). Cada modelo debe declarar formato, orden de muestras y latencia, y exportar vectores deterministas. Las pruebas van en `tests/`.

- `qpsk_rrc.py` (A01): símbolos QPSK ±1±1j con semilla, sobremuestreo 2× por inserción de ceros y 8 coeficientes RRCOS en la grilla ±0,25…±1,75 Ts. `python3 model/qpsk_rrc.py --seed 1` imprime la tabla de coeficientes y una secuencia de ejemplo. La normalización a energía unitaria es provisional hasta E02.
- `fir_time.py` (A02): FIR temporal flotante `fir_time(x, h)`, con historial inicial cero, una salida por muestra y sin cola, la misma convención que `frequency_filter` de E01. `python3 -m model.fir_time --seed 1` escribe en `build/a02/` un CSV por caso (impulso, ceros y QPSK 2×) con columnas `n,x_i,x_q,y_i,y_q`. El formato definitivo de vectores lo fija A05.
