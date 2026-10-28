`timescale 1ns/1ps

module frequency_output_select_onehot (
    input  logic        valid,
    input  logic        bank,
    input  logic [7:0]  select,
    input  logic [71:0] i0, i1, q0, q1,
    output logic [8:0]  out_i, out_q
);
    logic [71:0] bank_i, bank_q;
    logic [8:0] masked_i [0:7], masked_q [0:7];

    assign bank_i = bank ? i1 : i0;
    assign bank_q = bank ? q1 : q0;

    genvar k;
    generate
        for (k = 0; k < 8; k = k + 1) begin : select_word
            assign masked_i[k] = bank_i[k*9 +: 9] & {9{select[k]}};
            assign masked_q[k] = bank_q[k*9 +: 9] & {9{select[k]}};
        end
    endgenerate

    always_comb begin
        out_i = 9'd0;
        out_q = 9'd0;
        if (valid) begin
            for (integer k = 0; k < 8; k = k + 1) begin
                out_i = out_i | masked_i[k];
                out_q = out_q | masked_q[k];
            end
        end
    end
endmodule
