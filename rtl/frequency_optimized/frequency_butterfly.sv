`timescale 1ns/1ps

module frequency_butterfly #(
    parameter integer C_I = 256,
    parameter integer C_Q = 0,
    parameter integer REGISTER_PRODUCTS = 0
) (
    input  wire clk,
    input  wire rst,
    input  wire in_valid,
    input  wire signed [11:0] a_i,
    input  wire signed [11:0] a_q,
    input  wire signed [11:0] b_i,
    input  wire signed [11:0] b_q,
    output wire out_valid,
    output wire signed [11:0] sum_i,
    output wire signed [11:0] sum_q,
    output wire signed [11:0] diff_i,
    output wire signed [11:0] diff_q
);
    wire signed [11:0] aligned_i, aligned_q, t_i, t_q;
    wire signed [12:0] wide_sum_i, wide_sum_q, wide_diff_i, wide_diff_q;
    frequency_complex_const #(
        .C_I(C_I), .C_Q(C_Q), .REGISTER_PRODUCTS(REGISTER_PRODUCTS)
    ) u_product (
        .clk(clk), .rst(rst), .in_valid(in_valid), .a_i(b_i), .a_q(b_q),
        .out_valid(out_valid), .t_i(t_i), .t_q(t_q)
    );

    generate
        if (REGISTER_PRODUCTS) begin : pipeline
            reg signed [11:0] stored_i, stored_q;
            always @(posedge clk) begin
                if (!rst && in_valid) begin
                    stored_i <= a_i;
                    stored_q <= a_q;
                end
            end
            assign aligned_i = stored_i;
            assign aligned_q = stored_q;
        end else begin : direct
            assign aligned_i = a_i;
            assign aligned_q = a_q;
        end
    endgenerate

    assign wide_sum_i = $signed({aligned_i[11], aligned_i}) + $signed({t_i[11], t_i});
    assign wide_sum_q = $signed({aligned_q[11], aligned_q}) + $signed({t_q[11], t_q});
    assign wide_diff_i = $signed({aligned_i[11], aligned_i}) - $signed({t_i[11], t_i});
    assign wide_diff_q = $signed({aligned_q[11], aligned_q}) - $signed({t_q[11], t_q});
    assign sum_i = wide_sum_i[11:0];
    assign sum_q = wide_sum_q[11:0];
    assign diff_i = wide_diff_i[11:0];
    assign diff_q = wide_diff_q[11:0];

`ifndef SYNTHESIS
    always @(posedge clk) begin
        if (!rst && out_valid &&
            (wide_sum_i[12] != wide_sum_i[11] || wide_sum_q[12] != wide_sum_q[11] ||
             wide_diff_i[12] != wide_diff_i[11] || wide_diff_q[12] != wide_diff_q[11]))
            $fatal(1, "frequency_butterfly: butterfly overflows work");
    end
`endif
endmodule
