// B04: FIR temporal sistólico en forma transpuesta con la arquitectura de B03
// (docs/arquitectura-rtl-tiempo-optimizada.md) y la interfaz de E03.
module fir_time_systolic #(
    parameter int W_IN   = 2,  // entrada Q2.0 (E02)
    parameter int W_COEF = 8,  // coeficientes Q1.7 (A04)
    parameter int W_ACC  = 9   // sumas parciales y salida Q2.7 (A04)
) (
    input  logic                    clk,
    input  logic                    rst,
    input  logic signed [W_IN-1:0]  in_i,
    input  logic signed [W_IN-1:0]  in_q,
    input  logic                    in_valid,
    input  logic                    in_last,
    output logic                    in_ready,
    output logic signed [W_ACC-1:0] out_i,
    output logic signed [W_ACC-1:0] out_q,
    output logic                    out_valid,
    output logic                    out_last,
    input  logic                    out_ready
);

    // Tabla h_q[k] = round(h[k]·128) (A04, Q1.7): constantes, sin memoria.
    function automatic logic signed [W_COEF-1:0] coef(input int k);
        case (k)
            0:       coef = 1;
            1:       coef = -14;
            2:       coef = 14;
            3:       coef = 88;
            4:       coef = 88;
            5:       coef = 14;
            6:       coef = -14;
            default: coef = 1;
        endcase
    endfunction

    // Selección ±h / 0: con x en {-1, 0, +1} no hace falta multiplicador.
    function automatic logic signed [W_ACC-1:0] term(
        input logic signed [W_IN-1:0]   x,
        input logic signed [W_COEF-1:0] c
    );
        if (x == 0)
            term = 0;
        else if (x < 0)
            term = -c;  // x = -1
        else
            term = c;
    endfunction

    logic signed [W_ACC-1:0] s_i [1:7];  // s_k: aporte de x[n-1]…x[n-7] a salidas futuras
    logic signed [W_ACC-1:0] s_q [1:7];
    logic signed [W_ACC-1:0] y_i, y_q;   // registro de salida
    logic                    out_valid_r;
    logic                    last_r;
    logic                    acepta;

    // Regla 3: in_ready no depende de in_valid, y out_valid sale de un registro.
    // Hay lugar si la salida está vacía o se vacía en este mismo flanco.
    assign in_ready  = !rst && (!out_valid_r || out_ready);
    assign out_valid = out_valid_r && !rst;  // regla 6: 0 durante el reset
    assign acepta    = in_valid && in_ready;

    always_ff @(posedge clk) begin
        if (rst) begin
            // Regla 6: sumas parciales, salida y control a cero.
            y_i         <= 0;
            y_q         <= 0;
            last_r      <= 0;
            out_valid_r <= 0;
            for (int k = 1; k < 8; k++) begin
                s_i[k] <= 0;
                s_q[k] <= 0;
            end
        end else if (acepta) begin
            // Toda la ruta de datos avanza junta, solo al aceptar x[n] (reglas 1 y 7).
            y_i <= term(in_i, coef(0)) + s_i[1];  // y[n] = h0·x[n] + s1
            y_q <= term(in_q, coef(0)) + s_q[1];
            // Regla 5: con in_last las s_k pasan a 0 en este flanco y la muestra
            // siguiente arranca una trama nueva, sin bajar in_ready.
            for (int k = 1; k < 7; k++) begin  // s_k ← h_k·x[n] + s_(k+1)
                s_i[k] <= in_last ? '0 : term(in_i, coef(k)) + s_i[k+1];
                s_q[k] <= in_last ? '0 : term(in_q, coef(k)) + s_q[k+1];
            end
            s_i[7]      <= in_last ? '0 : term(in_i, coef(7));
            s_q[7]      <= in_last ? '0 : term(in_q, coef(7));
            last_r      <= in_last;
            out_valid_r <= 1;
        end else if (out_ready) begin
            out_valid_r <= 0;  // el receptor tomó y[n] y no entró otra muestra
        end
    end

    assign out_i    = y_i;
    assign out_q    = y_q;
    assign out_last = last_r;

endmodule
