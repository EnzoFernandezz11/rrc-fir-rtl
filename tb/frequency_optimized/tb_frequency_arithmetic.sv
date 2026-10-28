`timescale 1ns/1ps

module tb_frequency_arithmetic;
    reg clk = 0;
    always #5 clk = ~clk;
    reg rst = 1, enable = 0;
    reg signed [11:0] ai = 0, aq = 0, a12 = 0;
    reg signed [12:0] a13 = 0;
    wire signed [21:0] p12 [0:44];
    wire signed [22:0] p13 [0:44];
    wire signed [11:0] direct_i [0:31], direct_q [0:31];
    wire signed [11:0] piped_i [0:31], piped_q [0:31];
    wire [31:0] direct_valid, piped_valid, legal;
    wire signed [31:0] expected_i [0:31], expected_q [0:31];

    function automatic integer coefficient(input integer index);
        integer value;
        begin
            case (index/2)
                0:value=0; 1:value=1; 2:value=3; 3:value=4;
                4:value=11; 5:value=13; 6:value=27; 7:value=71;
                8:value=74; 9:value=98; 10:value=111; 11:value=139;
                12:value=178; 13:value=181; 14:value=186; 15:value=237;
                16:value=256; 17:value=278; 18:value=337; 19:value=355;
                20:value=356; default:value=511;
            endcase
            coefficient = index == 44 ? -512 : (index%2 ? -value : value);
        end
    endfunction
    function automatic integer cr(input integer index);
        begin
            if (index < 16) begin
                case (index%8)
                    0:cr=256; 1:cr=237; 2:cr=181; 3:cr=98;
                    4:cr=0; 5:cr=-98; 6:cr=-181; 7:cr=-237;
                endcase
            end else begin
                case (index-16)
                    0:cr=356; 1:cr=71; 2:cr=-337; 3:cr=-186;
                    4:cr=178; 5:cr=111; 6:cr=-11; 7:cr=13;
                    8:cr=0; 9:cr=13; 10:cr=-11; 11:cr=111;
                    12:cr=178; 13:cr=-186; 14:cr=-337; 15:cr=71;
                endcase
            end
        end
    endfunction
    function automatic integer ci(input integer index);
        integer value;
        begin
            if (index < 16) begin
                case (index%8)
                    0:value=0; 1:value=-98; 2:value=-181; 3:value=-237;
                    4:value=-256; 5:value=-237; 6:value=-181; 7:value=-98;
                endcase
                ci = index < 8 ? value : -value;
            end else begin
                case (index-16)
                    0:ci=0; 1:ci=-355; 2:ci=-139; 3:ci=278;
                    4:ci=178; 5:ci=-74; 6:ci=-27; 7:ci=-3;
                    8:ci=0; 9:ci=3; 10:ci=27; 11:ci=74;
                    12:ci=-178; 13:ci=-278; 14:ci=139; 15:ci=355;
                endcase
            end
        end
    endfunction
    function automatic integer corner(input integer index);
        begin
            case (index)
                0:corner=-2048; 1:corner=-2047; 2:corner=-1024; 3:corner=-1;
                4:corner=0; 5:corner=1; 6:corner=1024; 7:corner=2047;
            endcase
        end
    endfunction

    generate
        for (genvar k = 0; k < 45; k = k + 1) begin : csd
            frequency_csd_mul #(.COEF(coefficient(k))) u12(.a(a12), .p(p12[k]));
            frequency_csd_mul #(.A_WIDTH(13), .COEF(coefficient(k))) u13(.a(a13), .p(p13[k]));
        end
        for (genvar k = 0; k < 32; k = k + 1) begin : complex_products
            assign expected_i[k] = ($signed(ai)*cr(k) - $signed(aq)*ci(k) + 128) >>> 8;
            assign expected_q[k] = ($signed(ai)*ci(k) + $signed(aq)*cr(k) + 128) >>> 8;
            assign legal[k] = expected_i[k] >= -2048 && expected_i[k] <= 2047 &&
                              expected_q[k] >= -2048 && expected_q[k] <= 2047;
            frequency_complex_const #(.C_I(cr(k)), .C_Q(ci(k))) direct(
                .clk(clk), .rst(rst), .in_valid(enable && legal[k]), .a_i(ai), .a_q(aq),
                .out_valid(direct_valid[k]), .t_i(direct_i[k]), .t_q(direct_q[k]));
            frequency_complex_const #(.C_I(cr(k)), .C_Q(ci(k)), .REGISTER_PRODUCTS(1)) piped(
                .clk(clk), .rst(rst), .in_valid(enable && legal[k]), .a_i(ai), .a_q(aq),
                .out_valid(piped_valid[k]), .t_i(piped_i[k]), .t_q(piped_q[k]));
        end
    endgenerate

    integer n, k, expected, seed = 34;
    initial begin
        for (n = -4096; n < 4096; n = n + 1) begin
            a13 = n; a12 = n;
            #1;
            for (k = 0; k < 45; k = k + 1) begin
                expected = $signed(a12)*coefficient(k);
                if (p12[k] !== expected)
                    $fatal(1, "CSD12 coefficient=%0d a=%0d", coefficient(k), a12);
                expected = $signed(a13)*coefficient(k);
                if (p13[k] !== expected)
                    $fatal(1, "CSD13 coefficient=%0d a=%0d", coefficient(k), a13);
            end
        end
        for (n = 0; n < 4096; n = n + 1) begin
            @(negedge clk);
            rst = n == 70 || n == 301 || n == 1023;
            enable = n%7 != 0;
            if (n < 64) begin
                ai = corner(n/8); aq = corner(n%8);
            end else begin
                ai = $random(seed); aq = $random(seed);
            end
            #1;
            for (k = 0; k < 32; k = k + 1) begin
                if (direct_valid[k] !== (enable && legal[k] && !rst))
                    $fatal(1, "Combinational valid mismatch");
                if (direct_valid[k] && (direct_i[k] !== expected_i[k] || direct_q[k] !== expected_q[k]))
                    $fatal(1, "Direct product mismatch coefficient index=%0d a=(%0d,%0d)", k, ai, aq);
            end
            @(posedge clk); #1;
            for (k = 0; k < 32; k = k + 1) begin
                if (piped_valid[k] !== (enable && legal[k] && !rst))
                    $fatal(1, "Registered valid mismatch");
                if (piped_valid[k] && (piped_i[k] !== expected_i[k] || piped_q[k] !== expected_q[k]))
                    $fatal(1, "Registered product mismatch coefficient index=%0d a=(%0d,%0d)", k, ai, aq);
            end
        end
        $display("PASS frequency arithmetic: exhaustive CSD12/13, 32 complex constants, bubbles/reset");
        $finish;
    end
endmodule
