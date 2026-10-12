`timescale 1ns/1ps

module complex_mul_serial #(
    parameter int W_A = 32,
    parameter int W_B = 18,
    parameter int W_P = W_A + W_B + 1
) (
    input  logic                         clk,
    input  logic                         rst,
    input  logic                         start,
    input  logic signed [W_A-1:0]        a_i,
    input  logic signed [W_A-1:0]        a_q,
    input  logic signed [W_B-1:0]        b_i,
    input  logic signed [W_B-1:0]        b_q,
    output logic signed [W_P-1:0]        p_i,
    output logic signed [W_P-1:0]        p_q,
    output logic                         done
);

    localparam int W_REAL = W_A + W_B;

`ifndef SYNTHESIS
    initial begin
        if (W_A < 1 || W_B < 1 || W_P < W_REAL + 1)
            $fatal(1, "complex_mul_serial requires positive widths and W_P >= W_A+W_B+1");
    end
`endif

    logic load_operands;
    logic product_en;
    logic [1:0] product_index;
    logic combine_result;
    logic sel_a_q, sel_b_q;

    logic signed [W_A-1:0] op_a_i, op_a_q;
    logic signed [W_B-1:0] op_b_i, op_b_q;
    logic signed [W_A-1:0] mul_a;
    logic signed [W_B-1:0] mul_b;
    logic signed [W_REAL-1:0] mul_product;
    logic signed [W_REAL-1:0] prod_ii, prod_qq, prod_iq, prod_qi;
    logic signed [W_P-1:0] prod_ii_ext, prod_qq_ext, prod_iq_ext, prod_qi_ext;

    complex_mul_serial_control u_control (
        .clk,
        .rst,
        .start,
        .load_operands,
        .product_en,
        .product_index,
        .combine_result,
        .sel_a_q,
        .sel_b_q,
        .done
    );

    assign mul_a = sel_a_q ? op_a_q : op_a_i;
    assign mul_b = sel_b_q ? op_b_q : op_b_i;
    assign mul_product = mul_a * mul_b;

    assign prod_ii_ext = {{(W_P-W_REAL){prod_ii[W_REAL-1]}}, prod_ii};
    assign prod_qq_ext = {{(W_P-W_REAL){prod_qq[W_REAL-1]}}, prod_qq};
    assign prod_iq_ext = {{(W_P-W_REAL){prod_iq[W_REAL-1]}}, prod_iq};
    assign prod_qi_ext = {{(W_P-W_REAL){prod_qi[W_REAL-1]}}, prod_qi};

    always_ff @(posedge clk) begin
        if (rst) begin
            op_a_i  <= '0;
            op_a_q  <= '0;
            op_b_i  <= '0;
            op_b_q  <= '0;
            prod_ii <= '0;
            prod_qq <= '0;
            prod_iq <= '0;
            prod_qi <= '0;
            p_i     <= '0;
            p_q     <= '0;
        end else begin
            if (load_operands) begin
                op_a_i <= a_i;
                op_a_q <= a_q;
                op_b_i <= b_i;
                op_b_q <= b_q;
            end

            if (product_en) begin
                case (product_index)
                    2'd0: prod_ii <= mul_product;
                    2'd1: prod_qq <= mul_product;
                    2'd2: prod_iq <= mul_product;
                    2'd3: prod_qi <= mul_product;
                endcase
            end

            if (combine_result) begin
                p_i <= prod_ii_ext - prod_qq_ext;
                p_q <= prod_iq_ext + prod_qi_ext;
            end
        end
    end

endmodule
