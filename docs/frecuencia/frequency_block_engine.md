# Flujo de `frequency_block_engine`

Fuente: [`frequency_block_engine.sv`](../../rtl/frequency/frequency_block_engine.sv). El banco `work` contiene 16 muestras complejas Q7.5. Una sola instancia del multiplicador se comparte entre mariposas FFT/IFFT y productos espectrales.

```mermaid
flowchart TD
    LOAD["load_work = 1<br/>Flanco de carga"] --> ALIGN["Extender signo y alinear entrada<br/>input_to_work: desplazar F_WORK - F_IN"]
    ALIGN --> BITREV["work de bitrev4 de load_index<br/>Guardar I/Q; A04: entrada multiplicada por 32"]
    SELECT{"spectral_mode = 1?"}
    SELECT -->|Sí| BIN["addr_a = addr_b = bin_index<br/>Operando = work del bin<br/>Coeficiente = H del bin"]
    SELECT -->|No| BUTTERFLY["addr_a = table_a; addr_b = table_b<br/>Operando = work de addr_b<br/>Coeficiente = W; conjugado si inverse_mode"]
    BIN --> MUL["mul_start<br/>complex_mul_serial captura operandos<br/>Producto complejo completo: 23 bits, F = 13"]
    BUTTERFLY --> MUL
    MUL --> WAIT{"mul_done = 1?"}
    WAIT -->|No| WAIT
    WAIT -->|Sí| ROUND["Extender signo con bit de guarda<br/>rounded_product = producto + sesgo, luego corte<br/>A04: sumar 128 y desplazar 8 bits"]
    ROUND --> SPECTRAL{"write_bin = 1?"}
    SPECTRAL -->|Sí| WRITE_BIN["Guardar producto redondeado<br/>en work de bin_index"]
    SPECTRAL -->|No, capture_product = 1| CAPTURE["Registrar T en twiddled_i y twiddled_q"]
    CAPTURE --> WRITE["En el flanco siguiente: write_butterfly = 1<br/>work de addr_a = A + T<br/>work de addr_b = A - T"]
    WRITE --> CTRL["El control avanza operación o fase"]
    WRITE_BIN --> CTRL
    CTRL -->|Nueva multiplicación| SELECT
    CTRL -->|swap_work = 1| SWAP["Intercambiar work de swap_a y swap_b<br/>Una pareja por flanco; seis antes de IFFT"]
    SWAP --> CTRL
    CTRL -->|Última escritura IFFT| DONE["done del control = 1<br/>Banco completo y estable para emisión"]
    READ["Lectura combinacional: result_index"] --> RESULT["Seleccionar work de 8 + result_index<br/>Extender signo, redondear y escalar 1/16<br/>A04: sumar 2 y desplazar 2 bits"]
    RESULT --> OUT["result_i y result_q<br/>Q2.7, 9 bits por componente"]
    RST["rst = 1 en un flanco"] --> ZERO["Poner las 16 posiciones de work<br/>y twiddled_i/q en cero"]
```

La rama de carga se usa mientras el motor está libre. `load_work`, `capture_product`, `write_bin`, `write_butterfly` y `swap_work` habilitan escrituras en el flanco; sin habilitación se conservan los registros. El control las separa durante la operación normal. Las direcciones, coeficientes, sumas/restas y lectura de salida son combinacionales.

El redondeo se aplica después de completar cada producto complejo y al convertir la salida, sin saturación. Las comprobaciones de simulación detectan overflow; no forman parte del hardware sintetizado. El control decide cuándo el resultado leído es válido: durante el cálculo, las posiciones de `work` todavía pueden cambiar.

[Índice de diagramas](README.md) · [Control del motor](frequency_block_engine_control.md) · [ROMs](frequency_block_roms.md)
