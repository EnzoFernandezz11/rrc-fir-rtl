# Flujo de `fir_frequency_serial`

Fuente: [`fir_frequency_serial.sv`](../../rtl/frequency/fir_frequency_serial.sv). El núcleo conserva ocho muestras de historial y conecta su control con el motor. El primer diagrama muestra las escrituras de historial; el segundo, las conexiones combinacionales de carga y salida.

```mermaid
flowchart TD
    CLK["Flanco ascendente de clk"] --> RST{"rst = 1?"}
    RST -->|Sí| CLEAR["Poner history_i y history_q en cero<br/>8 posiciones"]
    RST -->|No| HC{"history_clear = 1?"}
    HC -->|Sí| CLEAR
    HC -->|No| HW{"history_write_en = 1?"}
    HW -->|Sí| WRITE["Guardar in_i e in_q en<br/>history de history_write_index"]
    HW -->|No| HOLD["Conservar historial"]
    CLEAR --> NEXT["Esperar próximo flanco"]
    WRITE --> NEXT
    HOLD --> NEXT
    NEXT --> CLK
```

```mermaid
flowchart TD
    CTRL["u_control: fir_frequency_serial_control"] --> LOAD["engine_load_en = history_copy_en<br/>o history_write_en o pad_en"]
    LOAD --> COPY{"history_copy_en?"}
    COPY -->|Sí| HISTORY["Índice 0 a 7<br/>Dato = history de history_copy_index"]
    COPY -->|No| INPUT{"history_write_en?"}
    INPUT -->|Sí| SAMPLE["Índice = 8 + history_write_index<br/>Dato = in_i e in_q"]
    INPUT -->|No| ZERO["Índice = 8 + pad_index<br/>Dato = cero; se carga solo si pad_en"]
    HISTORY --> ENGINE["u_engine: frequency_block_engine<br/>Carga habilitada por engine_load_en"]
    SAMPLE --> ENGINE
    ZERO --> ENGINE
    CTRL -->|engine_start| ENGINE
    CTRL -->|engine_result_index| ENGINE
    ENGINE -->|engine_done| CTRL
    ENGINE --> OUT["out_i y out_q = engine_result_i y engine_result_q<br/>Salida A04 Q2.7: 9 bits por componente"]
    CTRL --> FLAGS["in_ready, out_valid y out_last<br/>Gobiernan las transferencias externas"]
```

`history_clear` tiene prioridad sobre la escritura y se activa cuando se acepta la última salida de la trama. La copia usa el historial anterior; las entradas nuevas se escriben después, durante captura. En un bloque parcial, `pad_en` carga ceros en el motor sin agregarlos al historial. Con backpressure, el control conserva el índice de salida y el motor conserva `work`, por lo que I/Q permanecen estables.

[Índice de diagramas](README.md) · [Control del núcleo](fir_frequency_serial_control.md)
