# Vectores

Versionar solo vectores pequeños necesarios para reproducir las pruebas smoke, junto con configuración y semilla. Las regresiones grandes se generan en `build/`. No crear vectores definitivos hasta cerrar coeficientes, escala y formato en el [contrato](../docs/contratos/senales-y-formatos.md).

C02 genera vectores locales de A03/A04 en `build/frequency_serial_vectors.txt` con `python3 -m scripts.frequency_serial_vectors`; `make smoke` los regenera antes de simular. Incluyen cabecera de formatos, taps/H/W, cantidad de tramas, nombre y longitud de cada trama y filas enteras `x_i x_q y_i y_q`. El RTL compara las salidas aceptadas por índice con `fir_frequency_fxp`. Estos archivos generados no se versionan ni definen el formato común de A05.
