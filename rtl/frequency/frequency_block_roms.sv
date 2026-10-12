`timescale 1ns/1ps

module frequency_block_roms #(
    // TODO(A04): H and W use 16 fractional bits; regenerate these tables if that changes.
    parameter integer W_COEF = 18
) (
    input  logic [4:0] op_index,
    input  logic [3:0] bin_index,
    input  logic [2:0] swap_index,
    output logic [3:0] table_a,
    output logic [3:0] table_b,
    output logic signed [W_COEF-1:0] twiddle_i,
    output logic signed [W_COEF-1:0] twiddle_q,
    output logic signed [W_COEF-1:0] h_i,
    output logic signed [W_COEF-1:0] h_q,
    output logic [3:0] swap_a,
    output logic [3:0] swap_b
);
    logic [2:0] twiddle_index;

    always_comb begin
        table_a = 4'd0;
        table_b = 4'd1;
        twiddle_index = 3'd0;
        case (op_index)
            0:  begin table_a=0;  table_b=1;  twiddle_index=0; end
            1:  begin table_a=2;  table_b=3;  twiddle_index=0; end
            2:  begin table_a=4;  table_b=5;  twiddle_index=0; end
            3:  begin table_a=6;  table_b=7;  twiddle_index=0; end
            4:  begin table_a=8;  table_b=9;  twiddle_index=0; end
            5:  begin table_a=10; table_b=11; twiddle_index=0; end
            6:  begin table_a=12; table_b=13; twiddle_index=0; end
            7:  begin table_a=14; table_b=15; twiddle_index=0; end
            8:  begin table_a=0;  table_b=2;  twiddle_index=0; end
            9:  begin table_a=1;  table_b=3;  twiddle_index=4; end
            10: begin table_a=4;  table_b=6;  twiddle_index=0; end
            11: begin table_a=5;  table_b=7;  twiddle_index=4; end
            12: begin table_a=8;  table_b=10; twiddle_index=0; end
            13: begin table_a=9;  table_b=11; twiddle_index=4; end
            14: begin table_a=12; table_b=14; twiddle_index=0; end
            15: begin table_a=13; table_b=15; twiddle_index=4; end
            16: begin table_a=0;  table_b=4;  twiddle_index=0; end
            17: begin table_a=1;  table_b=5;  twiddle_index=2; end
            18: begin table_a=2;  table_b=6;  twiddle_index=4; end
            19: begin table_a=3;  table_b=7;  twiddle_index=6; end
            20: begin table_a=8;  table_b=12; twiddle_index=0; end
            21: begin table_a=9;  table_b=13; twiddle_index=2; end
            22: begin table_a=10; table_b=14; twiddle_index=4; end
            23: begin table_a=11; table_b=15; twiddle_index=6; end
            24: begin table_a=0;  table_b=8;  twiddle_index=0; end
            25: begin table_a=1;  table_b=9;  twiddle_index=1; end
            26: begin table_a=2;  table_b=10; twiddle_index=2; end
            27: begin table_a=3;  table_b=11; twiddle_index=3; end
            28: begin table_a=4;  table_b=12; twiddle_index=4; end
            29: begin table_a=5;  table_b=13; twiddle_index=5; end
            30: begin table_a=6;  table_b=14; twiddle_index=6; end
            31: begin table_a=7;  table_b=15; twiddle_index=7; end
        endcase
    end

    function automatic signed [W_COEF-1:0] w_real(input [2:0] index);
        begin
            case (index)
                0: w_real=18'sd65536;  1: w_real=18'sd60547;
                2: w_real=18'sd46341;  3: w_real=18'sd25080;
                4: w_real=18'sd0;      5: w_real=-18'sd25080;
                6: w_real=-18'sd46341; default: w_real=-18'sd60547;
            endcase
        end
    endfunction

    function automatic signed [W_COEF-1:0] w_imag(input [2:0] index);
        begin
            case (index)
                0: w_imag=18'sd0;       1: w_imag=-18'sd25080;
                2: w_imag=-18'sd46341;  3: w_imag=-18'sd60547;
                4: w_imag=-18'sd65536; 5: w_imag=-18'sd60547;
                6: w_imag=-18'sd46341; default: w_imag=-18'sd25080;
            endcase
        end
    endfunction

    function automatic signed [W_COEF-1:0] h_real(input [3:0] index);
        begin
            case (index)
                0: h_real=18'sd91794;   1: h_real=18'sd18127;
                2: h_real=-18'sd86187;  3: h_real=-18'sd47647;
                4: h_real=18'sd45897;   5: h_real=18'sd28513;
                6: h_real=-18'sd2739;   7: h_real=18'sd3875;
                8: h_real=18'sd0;       9: h_real=18'sd3875;
                10: h_real=-18'sd2739;  11: h_real=18'sd28513;
                12: h_real=18'sd45897;  13: h_real=-18'sd47647;
                14: h_real=-18'sd86187; default: h_real=18'sd18127;
            endcase
        end
    endfunction

    function automatic signed [W_COEF-1:0] h_imag(input [3:0] index);
        begin
            case (index)
                0: h_imag=18'sd0;       1: h_imag=-18'sd91131;
                2: h_imag=-18'sd35700;  3: h_imag=18'sd71309;
                4: h_imag=18'sd45897;   5: h_imag=-18'sd19051;
                6: h_imag=-18'sd6612;   7: h_imag=-18'sd771;
                8: h_imag=18'sd0;       9: h_imag=18'sd771;
                10: h_imag=18'sd6612;   11: h_imag=18'sd19051;
                12: h_imag=-18'sd45897; 13: h_imag=-18'sd71309;
                14: h_imag=18'sd35700;  default: h_imag=18'sd91131;
            endcase
        end
    endfunction

    function automatic [3:0] reverse_left(input [2:0] index);
        begin
            case (index)
                0: reverse_left=4'd1;  1: reverse_left=4'd2;
                2: reverse_left=4'd3;  3: reverse_left=4'd5;
                4: reverse_left=4'd7;  default: reverse_left=4'd11;
            endcase
        end
    endfunction

    function automatic [3:0] reverse_right(input [2:0] index);
        begin
            case (index)
                0: reverse_right=4'd8;  1: reverse_right=4'd4;
                2: reverse_right=4'd12; 3: reverse_right=4'd10;
                4: reverse_right=4'd14; default: reverse_right=4'd13;
            endcase
        end
    endfunction

    always_comb begin
        twiddle_i = w_real(twiddle_index);
        twiddle_q = w_imag(twiddle_index);
        h_i = h_real(bin_index);
        h_q = h_imag(bin_index);
        swap_a = reverse_left(swap_index);
        swap_b = reverse_right(swap_index);
    end
endmodule
