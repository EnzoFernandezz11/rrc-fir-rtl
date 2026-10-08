# Modelos Python

A implementará aquí QPSK, generación de coeficientes, filtros flotantes y versiones de punto fijo según los [contratos](../docs/contrato-tecnico.md#3-detalle-por-tema). Cada modelo debe declarar formato, orden de muestras y latencia, y exportar vectores deterministas. Las pruebas van en `tests/`.

- `qpsk_rrc.py` (A01/E02): símbolos QPSK ±1±1j con semilla, upsampling 2× por inserción de ceros y 8 coeficientes RRCOS en la grilla ±0,25…±1,75 Ts. `python3 model/qpsk_rrc.py --seed 1` imprime la tabla de coeficientes y una secuencia de ejemplo. La normalización a energía unitaria sigue propuesta hasta la revisión conjunta de E02.
- `frequency.py` (E01/C01): modelo flotante reutilizable `frequency_filter(signal, taps)`. Recibe una trama de muestras complejas y ocho coeficientes en orden causal; devuelve una salida por muestra, con historial inicial cero y sin cola final. Cada llamada procesa una trama independiente completa. Representa FFT16/IFFT16 mediante DFT directa, sin latencia de reloj. La [prueba de E01](../tests/test_frequency_overlap_contract.py) compara la salida con una convolución causal independiente y usa los estímulos de A01/E02.
