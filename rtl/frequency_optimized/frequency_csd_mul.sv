`timescale 1ns/1ps

module frequency_csd_mul #(
    parameter integer A_WIDTH = 12,
    parameter integer COEF = 256
) (
    input  wire signed [A_WIDTH-1:0] a,
    output wire signed [A_WIDTH+9:0] p
);
    localparam integer W = A_WIDTH + 10;

    function automatic integer digit(input integer position);
        integer remaining, d, i;
        begin
            remaining = (COEF < 0) ? -COEF : COEF;
            d = 0;
            for (i = 0; i <= position; i = i + 1) begin
                d = 0;
                if (remaining % 2)
                    d = ((remaining % 4) == 1) ? 1 : -1;
                remaining = (remaining - d) / 2;
            end
            digit = (COEF < 0) ? -d : d;
        end
    endfunction

    wire signed [W-1:0] extended_a = {{10{a[A_WIDTH-1]}}, a};
    wire signed [W-1:0] tree [1:31];
    genvar n;
    generate
        for (n = 0; n < 16; n = n + 1) begin : leaves
            if (digit(n) == 1)
                assign tree[16+n] = extended_a <<< n;
            else if (digit(n) == -1)
                assign tree[16+n] = -(extended_a <<< n);
            else
                assign tree[16+n] = '0;
        end
        for (n = 1; n < 16; n = n + 1) begin : sums
            assign tree[n] = tree[2*n] + tree[2*n+1];
        end
    endgenerate
    assign p = tree[1];

`ifndef SYNTHESIS
    initial begin
        if ((A_WIDTH != 12 && A_WIDTH != 13) || COEF < -512 || COEF > 511)
            $fatal(1, "frequency_csd_mul: unsupported width or coefficient");
    end
`endif
endmodule
