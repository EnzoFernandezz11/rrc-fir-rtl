`timescale 1ns/1ps

module frequency_fft16 #(
    parameter integer INVERSE = 0
) (
    input  wire clk,
    input  wire rst,
    input  wire in_valid,
    input  wire [191:0] in_i,
    input  wire [191:0] in_q,
    output wire out_valid,
    output wire [191:0] out_i,
    output wire [191:0] out_q
);
    wire [191:0] stage_i [0:4];
    wire [191:0] stage_q [0:4];
    wire [4:0] stage_valid;

    function automatic integer bitrev(input integer n);
        begin bitrev = ((n&1)<<3) | ((n&2)<<1) | ((n&4)>>1) | ((n&8)>>3); end
    endfunction
    function automatic integer wr(input integer k);
        begin
            case (k)
                0:wr=256; 1:wr=237; 2:wr=181; 3:wr=98;
                4:wr=0; 5:wr=-98; 6:wr=-181; 7:wr=-237;
                default:wr=0;
            endcase
        end
    endfunction
    function automatic integer wi(input integer k);
        integer value;
        begin
            case (k)
                0:value=0; 1:value=-98; 2:value=-181; 3:value=-237;
                4:value=-256; 5:value=-237; 6:value=-181; 7:value=-98;
                default:value=0;
            endcase
            wi = INVERSE ? -value : value;
        end
    endfunction

    assign stage_valid[0] = in_valid && !rst;
    generate
        for (genvar n = 0; n < 16; n = n + 1) begin : permutation
            assign stage_i[0][12*n +: 12] = in_i[12*bitrev(n) +: 12];
            assign stage_q[0][12*n +: 12] = in_q[12*bitrev(n) +: 12];
        end
        for (genvar s = 0; s < 4; s = s + 1) begin : stages
            localparam integer HALF = 1 << s;
            wire [191:0] result_i, result_q;
            wire [7:0] result_valid;
            for (genvar n = 0; n < 8; n = n + 1) begin : butterflies
                localparam integer A = (n/HALF)*2*HALF + n%HALF;
                localparam integer B = A + HALF;
                localparam integer K = (n%HALF)*(8/HALF);
                frequency_butterfly #(
                    .C_I(wr(K)), .C_Q(wi(K)), .REGISTER_PRODUCTS(s >= 2)
                ) u_butterfly (
                    .clk(clk), .rst(rst), .in_valid(stage_valid[s]),
                    .a_i(stage_i[s][12*A +: 12]), .a_q(stage_q[s][12*A +: 12]),
                    .b_i(stage_i[s][12*B +: 12]), .b_q(stage_q[s][12*B +: 12]),
                    .out_valid(result_valid[n]),
                    .sum_i(result_i[12*A +: 12]), .sum_q(result_q[12*A +: 12]),
                    .diff_i(result_i[12*B +: 12]), .diff_q(result_q[12*B +: 12])
                );
            end
            if (s < 3) begin : capture
                reg valid;
                reg [191:0] data_i, data_q;
                always @(posedge clk) begin
                    if (rst)
                        valid <= 1'b0;
                    else begin
                        valid <= result_valid[0];
                        if (result_valid[0]) begin
                            data_i <= result_i;
                            data_q <= result_q;
                        end
                    end
                end
                assign stage_valid[s+1] = valid && !rst;
                assign stage_i[s+1] = data_i;
                assign stage_q[s+1] = data_q;
            end else begin : destination
                // The reserved X / useful-IFFT bank owns the sixth capture.
                assign stage_valid[s+1] = result_valid[0];
                assign stage_i[s+1] = result_i;
                assign stage_q[s+1] = result_q;
            end
        end
    endgenerate
    assign out_valid = stage_valid[4];
    assign out_i = stage_i[4];
    assign out_q = stage_q[4];

`ifndef SYNTHESIS
    initial begin
        if (INVERSE != 0 && INVERSE != 1)
            $fatal(1, "frequency_fft16: INVERSE must be 0 or 1");
    end
`endif
endmodule
