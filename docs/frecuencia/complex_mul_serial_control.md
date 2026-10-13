# Flujo de `complex_mul_serial_control`

Fuente: [`complex_mul_serial_control.sv`](../../rtl/frequency/complex_mul_serial_control.sv). La FSM captura ambos operandos complejos, habilita cuatro productos reales y genera un pulso registrado de finalización.

```mermaid
flowchart TD
    RST["rst = 1 en un flanco<br/>done = 0"] --> IDLE["IDLE"]
    IDLE --> START{"start = 1?"}
    START -->|No| IDLE
    START -->|Sí| CAPTURE["load_operands = 1<br/>Capturar operandos en el flanco"]
    CAPTURE --> II["MUL_II<br/>product_en = 1; product_index = 0<br/>sel_a_q = 0; sel_b_q = 0"]
    II --> QQ["MUL_QQ<br/>product_en = 1; product_index = 1<br/>sel_a_q = 1; sel_b_q = 1"]
    QQ --> IQ["MUL_IQ<br/>product_en = 1; product_index = 2<br/>sel_a_q = 0; sel_b_q = 1"]
    IQ --> QI["MUL_QI<br/>product_en = 1; product_index = 3<br/>sel_a_q = 1; sel_b_q = 0"]
    QI --> FINISH["En el flanco: completar cuarto producto<br/>done = 1"]
    FINISH --> DONE["DONE<br/>Producto final disponible durante este ciclo"]
    DONE --> LOWER["En el siguiente flanco: done = 0<br/>El consumidor captura el resultado"]
    LOWER --> IDLE
```

Reset tiene prioridad desde cualquier estado y vuelve a `IDLE` con `done=0`; el datapath limpia operandos y resultados en ese mismo flanco. `start` se acepta únicamente en `IDLE`. Los estados de producto avanzan un estado por flanco y `DONE` vuelve a `IDLE` sin aceptar un nuevo `start` en ese flanco. Un estado inválido también vuelve a `IDLE`.

Contando el flanco que acepta `start` como 1: captura en 1, productos en 2…5, resultado completo y `done=1` después del flanco 5; el motor lo captura en el 6. `done` se pone por defecto en cero en cada flanco y solo sube en la transición `MUL_QI → DONE`. No existe el estado `COMBINE`.

[Índice de diagramas](README.md) · [Datapath del multiplicador](complex_mul_serial.md)
