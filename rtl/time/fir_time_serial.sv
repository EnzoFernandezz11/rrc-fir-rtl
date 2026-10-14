// B02: FIR temporal serial con la arquitectura de B01
// (docs/arquitectura-rtl-tiempo-serial.md) y la interfaz de E03.
module fir_time_serial #(
    parameter int W_IN   = 2,  // entrada Q2.0 (E02)
    parameter int W_COEF = 8,  // coeficientes Q1.7 (A04)
    parameter int W_ACC  = 9   // acumulador y salida Q2.7 (A04)
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

    typedef enum logic [1:0] {
        IDLE, 
        MAC, 
        OUT
    } state_t;
    state_t state;

    // Regla 3: in_ready y out_valid dependen solo del estado y de rst.
    assign in_ready  = (state == IDLE) && !rst;
    assign out_valid = (state == OUT)  && !rst;

    logic signed [W_IN-1:0]   hist_i [0:7];  // hist[k] = x[n-k]
    logic signed [W_IN-1:0]   hist_q [0:7];
    logic        [2:0]        k;
    logic signed [W_COEF-1:0] coef;
    logic signed [W_IN-1:0]   x_i_k, x_q_k;
    logic signed [W_COEF-1:0] term_i, term_q;

    // Mux 8:1: x[n-k] según el contador.
    assign x_i_k = hist_i[k];
    assign x_q_k = hist_q[k];

    // Tabla h_q[k] = round(h[k]·128) (A04, Q1.7): constantes, sin memoria.
    always_comb begin
        case (k)
            3'd0: coef = 1;
            3'd1: coef = -14;
            3'd2: coef = 14;
            3'd3: coef = 88;
            3'd4: coef = 88;
            3'd5: coef = 14;
            3'd6: coef = -14;
            3'd7: coef = 1;
        endcase
    end

    // Selección ±h / 0: con x en {-1, 0, +1} no hace falta multiplicador.
    always_comb begin
        if (x_i_k == 0)         
            term_i = 0;
        else if (x_i_k < 0)
            term_i = -coef;  // x = -1
        else                    
            term_i = coef;
            
        if (x_q_k == 0)         
            term_q = 0;
        else if (x_q_k < 0)
            term_q = -coef;
        else                    
            term_q = coef;
    end

    logic signed [W_ACC-1:0] acc_i, acc_q;
    logic                    last_r;

    always_ff @(posedge clk) begin
        if (rst) begin
            // Regla 6: todo a cero y estado inicial.
            state  <= IDLE;
            k      <= 0;
            acc_i  <= 0;
            acc_q  <= 0;
            last_r <= 0;
            for (int j = 0; j < 8; j++) begin
                hist_i[j] <= 0;
                hist_q[j] <= 0;
            end
        end else begin
            case (state)
                IDLE: 
                if (in_valid) begin
                    // Acepta x[n]: entra en la posición 0 y el resto corre.
                    hist_i[0] <= in_i;
                    hist_q[0] <= in_q;
                    for (int j = 1; j < 8; j++) begin
                        hist_i[j] <= hist_i[j-1];
                        hist_q[j] <= hist_q[j-1];
                    end
                    acc_i  <= 0;
                    acc_q  <= 0;
                    k      <= 0;
                    last_r <= in_last;
                    state  <= MAC;
                end
                MAC: 
                begin
                    // Un tap por ciclo en I y Q a la vez.
                    acc_i <= acc_i + term_i;
                    acc_q <= acc_q + term_q;
                    k     <= k + 1;
                    if (k == 3'd7) state <= OUT;
                end
                OUT: 
                if (out_ready) begin
                    // Entrega y[n]; si era el último de la trama, limpia el historial.
                    state <= IDLE;
                    if (last_r) begin
                        for (int j = 0; j < 8; j++) begin
                            hist_i[j] <= 0;
                            hist_q[j] <= 0;
                        end
                    end
                end
                default: state <= IDLE;
            endcase
        end
    end

    // Los acumuladores son también los registros de salida.
    assign out_i    = acc_i;
    assign out_q    = acc_q;
    assign out_last = last_r;

endmodule
