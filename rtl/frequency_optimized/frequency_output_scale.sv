`timescale 1ns/1ps

// The reserved output bank owns the conversion register and overflow check.
module frequency_output_scale (
    input wire [95:0] in_i, in_q,
    output wire [71:0] out_i, out_q
);
    genvar k;
    generate
        for (k = 0; k < 8; k = k + 1) begin : samples
            wire signed [12:0] rounded_i, rounded_q;
            assign rounded_i = ($signed({in_i[k*12+11], in_i[k*12 +: 12]}) + 13'sd2) >>> 2;
            assign rounded_q = ($signed({in_q[k*12+11], in_q[k*12 +: 12]}) + 13'sd2) >>> 2;
            assign out_i[k*9 +: 9] = rounded_i[8:0];
            assign out_q[k*9 +: 9] = rounded_q[8:0];
        end
    endgenerate
endmodule
