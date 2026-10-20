`timescale 1ns/1ps

// One fixed H per bin; Y banks own the second (final) register.
module frequency_spectral16 (
    input logic clk, rst, in_valid,
    input logic [191:0] in_i, in_q,
    output logic out_valid,
    output wire [191:0] out_i, out_q
);
    function automatic integer h_real(input integer bin_index);
        case (bin_index)
            0: h_real = 356;
            1: h_real = 71;
            2: h_real = -337;
            3: h_real = -186;
            4: h_real = 178;
            5: h_real = 111;
            6: h_real = -11;
            7: h_real = 13;
            8: h_real = 0;
            9: h_real = 13;
            10: h_real = -11;
            11: h_real = 111;
            12: h_real = 178;
            13: h_real = -186;
            14: h_real = -337;
            15: h_real = 71;
            default: h_real = 0;
        endcase
    endfunction

    function automatic integer h_imag(input integer bin_index);
        case (bin_index)
            0: h_imag = 0;
            1: h_imag = -355;
            2: h_imag = -139;
            3: h_imag = 278;
            4: h_imag = 178;
            5: h_imag = -74;
            6: h_imag = -27;
            7: h_imag = -3;
            8: h_imag = 0;
            9: h_imag = 3;
            10: h_imag = 27;
            11: h_imag = 74;
            12: h_imag = -178;
            13: h_imag = -278;
            14: h_imag = 139;
            15: h_imag = 355;
            default: h_imag = 0;
        endcase
    endfunction

    wire [15:0] bin_valid;
    genvar k;
    generate
        for (k = 0; k < 16; k = k + 1) begin : spectral_bins
            frequency_complex_const #(
                .C_I(h_real(k)), .C_Q(h_imag(k)), .REGISTER_PRODUCTS(1)
            ) u_product (
                .clk(clk), .rst(rst), .in_valid(in_valid),
                .a_i(in_i[k*12 +: 12]), .a_q(in_q[k*12 +: 12]),
                .out_valid(bin_valid[k]), .t_i(out_i[k*12 +: 12]), .t_q(out_q[k*12 +: 12])
            );
        end
    endgenerate
    assign out_valid = bin_valid[0];
endmodule
