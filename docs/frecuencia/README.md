# Diagramas del RTL en frecuencia

Los diagramas corresponden a los siete módulos actuales de [`rtl/frequency`](../../rtl/frequency), con multiplicador acumulador y formatos A04. Están escritos en Mermaid para visualizarlos en GitHub o en un visor Markdown compatible.

| Módulo | Responsabilidad | Diagrama |
|---|---|---|
| `fir_frequency_serial` | Historial, selección de carga y conexión con el motor | [Flujo del núcleo](fir_frequency_serial.md) |
| `fir_frequency_serial_control` | Captura, relleno, cálculo y emisión con handshake | [Control del núcleo](fir_frequency_serial_control.md) |
| `frequency_block_engine` | Banco de trabajo, mariposa, productos y cortes numéricos | [Flujo del motor](frequency_block_engine.md) |
| `frequency_block_engine_control` | Secuencia FFT → H → permutación → IFFT | [Control del motor](frequency_block_engine_control.md) |
| `frequency_block_roms` | Lectura combinacional de operaciones, H, W e intercambios | [Flujo de las ROMs](frequency_block_roms.md) |
| `complex_mul_serial` | Cuatro productos reales acumulados en I/Q | [Flujo del multiplicador](complex_mul_serial.md) |
| `complex_mul_serial_control` | Captura de operandos y secuencia de multiplicación | [Control del multiplicador](complex_mul_serial_control.md) |

En los bloques con reloj, las escrituras ocurren en el flanco ascendente y el reset es síncrono activo alto. Los rombos representan condiciones; no agregan ciclos. Los estados de control conservan los nombres del RTL. Los datapaths actúan según las habilitaciones de sus controles, y las ROMs no tienen reloj ni estados.

El [diagrama general](general_diagram.md) muestra el algoritmo completo; la [arquitectura serial](../arquitectura-rtl-frecuencia-serial.md) documenta interfaces, formatos y presupuesto de ciclos. Con entrada disponible y salida lista: 7 ciclos por mariposa, 6 por bin, 550 de motor y 575 por bloque completo.
