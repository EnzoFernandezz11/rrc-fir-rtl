# Modelos Python

A implementará aquí QPSK, generación de coeficientes, filtros flotantes y versiones de punto fijo según los [contratos](../docs/contrato-tecnico.md#3-detalle-por-tema). Cada modelo debe declarar formato, orden de muestras y latencia, y exportar vectores deterministas. Las pruebas van en `tests/`.

- `qpsk_rrc.py` (A01): símbolos QPSK ±1±1j con semilla, sobremuestreo 2× por inserción de ceros y 8 coeficientes RRCOS en la grilla ±0,25…±1,75 Ts. `python3 model/qpsk_rrc.py --seed 1` imprime la tabla de coeficientes y una secuencia de ejemplo. La normalización a energía unitaria es provisional hasta E02.
