# Flujo de `frequency_block_engine_control`

Fuente: [`frequency_block_engine_control.sv`](../../rtl/frequency/frequency_block_engine_control.sv). La FSM tiene cinco estados y tres fases: `PH_FFT`, `PH_MUL` y `PH_IFFT`. `op_index` recorre las 32 mariposas, `bin_index` los 16 productos espectrales y `swap_index` los seis intercambios.

```mermaid
flowchart TD
    RST["rst = 1 en un flanco<br/>phase = PH_FFT<br/>Índices = 0; done = 0"] --> IDLE["ST_IDLE<br/>load_work = load_en"]
    IDLE --> START{"start = 1?"}
    START -->|No| IDLE
    START -->|Sí| FIRST["phase = PH_FFT<br/>op_index = 0; bin_index = 0<br/>mul_start = 1 en ST_IDLE con start"]
    FIRST --> WAIT["ST_WAIT<br/>Esperar multiplicador"]
    LAUNCH["ST_LAUNCH<br/>mul_start = 1"] --> WAIT
    WAIT --> MUL_DONE{"mul_done = 1?"}
    MUL_DONE -->|No| WAIT
    MUL_DONE -->|Sí| PHASE{"phase = PH_MUL?"}
    PHASE -->|Sí| BIN_WRITE["write_bin = 1<br/>Escribir bin_index"]
    BIN_WRITE --> LAST_BIN{"bin_index = 15?"}
    LAST_BIN -->|No| BIN_INC["bin_index += 1"] --> LAUNCH
    LAST_BIN -->|Sí| INVERSE["phase = PH_IFFT<br/>op_index = 0; swap_index = 0"]
    INVERSE --> REORDER["ST_REORDER<br/>swap_work = 1<br/>Intercambiar pareja swap_index"]
    REORDER --> LAST_SWAP{"swap_index = 5?"}
    LAST_SWAP -->|No| SWAP_INC["swap_index += 1"] --> REORDER
    LAST_SWAP -->|Sí| OP_ZERO["op_index = 0"] --> LAUNCH
    PHASE -->|No: FFT o IFFT| CAPTURE["capture_product = 1<br/>Registrar T"]
    CAPTURE --> WRITE["ST_WRITE<br/>write_butterfly = 1<br/>Escribir A + T y A - T"]
    WRITE --> LAST_OP{"op_index = 31?"}
    LAST_OP -->|No| OP_INC["op_index += 1"] --> LAUNCH
    LAST_OP -->|Sí| IFFT{"phase = PH_IFFT?"}
    IFFT -->|No| SPECTRUM["phase = PH_MUL<br/>bin_index = 0"] --> LAUNCH
    IFFT -->|Sí| COMPLETE["done = 1 por un ciclo<br/>phase = PH_FFT; op_index = 0"] --> IDLE
```

`spectral_mode` indica `PH_MUL`; `inverse_mode` indica `PH_IFFT`. Ambos son combinacionales. Reset tiene prioridad desde cualquier estado. `done` se pone por defecto en cero en cada flanco y sube al escribir la última mariposa IFFT; un estado inválido vuelve a `ST_IDLE`.

La primera multiplicación arranca en el mismo flanco que acepta `start`, sin pasar por `ST_LAUNCH`. Después, cada mariposa captura T en `ST_WAIT` y escribe en `ST_WRITE`; cada bin se escribe directamente en `ST_WAIT`. Las cajas intermedias de actualización no son estados adicionales. El motor necesita 32 × 7 + 16 × 6 + 6 + 32 × 7 = 550 ciclos según el conteo del testbench.

[Índice de diagramas](README.md) · [Datapath del motor](frequency_block_engine.md)
