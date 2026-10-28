`timescale 1ns/1ps

module frequency_complex_const #(
    parameter integer C_I = 256,
    parameter integer C_Q = 0,
    parameter integer REGISTER_PRODUCTS = 0
) (
    input  wire clk,
    input  wire rst,
    input  wire in_valid,
    input  wire signed [11:0] a_i,
    input  wire signed [11:0] a_q,
    output wire out_valid,
    output wire signed [11:0] t_i,
    output wire signed [11:0] t_q
);
    localparam integer EQUAL = (C_I != 0) && ((C_I == C_Q) || (C_I == -C_Q));
    localparam integer GENERAL = (C_I != 0) && (C_Q != 0) && !EQUAL;
    wire signed [22:0] product [0:3];
    wire signed [22:0] aligned [0:3];
    wire signed [22:0] combined_i, combined_q;
    wire signed [23:0] rounded_i, rounded_q;

    generate
        if (C_I == 0 && C_Q == 0) begin : zero
            assign product[0] = '0;
            assign product[1] = '0;
            assign product[2] = '0;
            assign product[3] = '0;
        end else if (C_I == 0 || C_Q == 0) begin : axis
            wire signed [21:0] pi, pq;
            frequency_csd_mul #(.COEF(C_Q == 0 ? C_I : C_Q)) u_i(.a(a_i), .p(pi));
            frequency_csd_mul #(.COEF(C_Q == 0 ? C_I : C_Q)) u_q(.a(a_q), .p(pq));
            assign product[0] = {{1{pi[21]}}, pi};
            assign product[1] = {{1{pq[21]}}, pq};
            assign product[2] = '0;
            assign product[3] = '0;
        end else if (EQUAL) begin : factored
            wire signed [12:0] ai = {a_i[11], a_i};
            wire signed [12:0] aq = {a_q[11], a_q};
            wire signed [12:0] pre_i = (C_I == C_Q) ? ai-aq : ai+aq;
            wire signed [12:0] pre_q = (C_I == C_Q) ? aq+ai : aq-ai;
            frequency_csd_mul #(.A_WIDTH(13), .COEF(C_I)) u_i(.a(pre_i), .p(product[0]));
            frequency_csd_mul #(.A_WIDTH(13), .COEF(C_I)) u_q(.a(pre_q), .p(product[1]));
            assign product[2] = '0;
            assign product[3] = '0;
        end else begin : general
            wire signed [21:0] m0, m1, m2, m3;
            frequency_csd_mul #(.COEF(C_I)) u_0(.a(a_i), .p(m0));
            frequency_csd_mul #(.COEF(C_Q)) u_1(.a(a_q), .p(m1));
            frequency_csd_mul #(.COEF(C_Q)) u_2(.a(a_i), .p(m2));
            frequency_csd_mul #(.COEF(C_I)) u_3(.a(a_q), .p(m3));
            assign product[0] = {m0[21], m0};
            assign product[1] = {m1[21], m1};
            assign product[2] = {m2[21], m2};
            assign product[3] = {m3[21], m3};
        end
        if (REGISTER_PRODUCTS) begin : pipeline
            reg valid;
            reg signed [22:0] stored [0:3];
            integer n;
            always @(posedge clk) begin
                if (rst)
                    valid <= 1'b0;
                else begin
                    valid <= in_valid;
                    if (in_valid)
                        for (n = 0; n < 4; n = n + 1)
                            stored[n] <= product[n];
                end
            end
            for (genvar k = 0; k < 4; k = k + 1) begin : outputs
                assign aligned[k] = stored[k];
            end
            assign out_valid = valid && !rst;
        end else begin : direct
            for (genvar k = 0; k < 4; k = k + 1) begin : outputs
                assign aligned[k] = product[k];
            end
            assign out_valid = in_valid && !rst;
        end
    endgenerate

    assign combined_i = GENERAL ? aligned[0]-aligned[1] :
                        (C_I == 0 && C_Q != 0) ? -aligned[1] : aligned[0];
    assign combined_q = GENERAL ? aligned[2]+aligned[3] :
                        (C_I == 0 && C_Q != 0) ? aligned[0] : aligned[1];
    assign rounded_i = ($signed({combined_i[22], combined_i}) + 24'sd128) >>> 8;
    assign rounded_q = ($signed({combined_q[22], combined_q}) + 24'sd128) >>> 8;
    assign t_i = rounded_i[11:0];
    assign t_q = rounded_q[11:0];

`ifndef SYNTHESIS
    initial begin
        if (C_I < -512 || C_I > 511 || C_Q < -512 || C_Q > 511 ||
            (REGISTER_PRODUCTS != 0 && REGISTER_PRODUCTS != 1))
            $fatal(1, "frequency_complex_const: unsupported parameter");
    end
    always @(posedge clk) begin
        if (!rst && out_valid &&
            (rounded_i != $signed(t_i) || rounded_q != $signed(t_q)))
            $fatal(1, "frequency_complex_const: product overflows work");
    end
`endif
endmodule
