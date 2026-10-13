# Flujo de `complex_mul_serial`

Fuente: [`complex_mul_serial.sv`](../../rtl/frequency/complex_mul_serial.sv). El datapath captura operandos y reutiliza un único multiplicador real. Los cuatro productos se acumulan directamente en `p_i/p_q`, sin registros de productos separados ni ciclo de combinación.

```mermaid
flowchart TD
    CLK["Flanco ascendente de clk"] --> RST{"rst = 1?"}
    RST -->|Sí| CLEAR["Operandos registrados = 0<br/>p_i = 0; p_q = 0"]
    RST -->|No| LOAD{"load_operands = 1?"}
    LOAD -->|Sí| CAPTURE["Registrar a_i, a_q, b_i y b_q"]
    LOAD -->|No| PRODUCT{"product_en = 1?"}
    CAPTURE --> PRODUCT
    PRODUCT -->|No| HOLD["Conservar p_i y p_q"]
    PRODUCT -->|Sí| SELECT["Seleccionar operandos registrados<br/>mul_a según sel_a_q<br/>mul_b según sel_b_q"]
    SELECT --> MUL["mul_product = mul_a × mul_b<br/>Ancho completo W_A + W_B"]
    MUL --> EXTEND["Extender signo del producto a W_P"]
    EXTEND --> INDEX{"product_index?"}
    INDEX -->|0: ai × bi| II["p_i = mul_product_ext"]
    INDEX -->|1: aq × bq| QQ["p_i = p_i - mul_product_ext"]
    INDEX -->|2: ai × bq| IQ["p_q = mul_product_ext"]
    INDEX -->|3: aq × bi| QI["p_q = p_q + mul_product_ext"]
    CLEAR --> NEXT["Esperar próximo flanco"]
    HOLD --> NEXT
    II --> NEXT
    QQ --> NEXT
    IQ --> NEXT
    QI --> NEXT
    NEXT --> CLK
```

El control separa la captura de los cuatro ciclos de producto. Los multiplexores, la multiplicación y la extensión de signo son combinacionales; solo se registran los operandos y las actualizaciones de `p_i/p_q` indicadas en el diagrama. `load_operands` y `product_en` son habilitaciones independientes en el datapath, aunque el control no las activa juntas.

`W_P` debe ser al menos `W_A + W_B + 1` para cubrir la suma/resta completa. El motor instancia la unidad con anchos 12 × 10 → 23 bits; el redondeo A04 se hace en el motor, después de `done`. Durante el cálculo las salidas pueden mostrar valores parciales; son finales con `done` y se mantienen hasta la siguiente acumulación o reset.

[Índice de diagramas](README.md) · [Control del multiplicador](complex_mul_serial_control.md)
