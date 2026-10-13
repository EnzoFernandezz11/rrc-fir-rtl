`timescale 1ns/1ps

module frequency_block_engine #(
    parameter integer W_IN   = 2,
    parameter integer F_IN   = 0,
    parameter integer W_WORK = 12,
    parameter integer F_WORK = 5,
    parameter integer W_COEF = 10,
    parameter integer F_COEF = 8,
    parameter integer W_OUT  = 9,
    parameter integer F_OUT  = 7
) (
    input  logic                         clk,
    input  logic                         rst,
    input  logic                         load_en,
    input  logic [3:0]                   load_index,
    input  logic signed [W_IN-1:0]       load_i,
    input  logic signed [W_IN-1:0]       load_q,
    input  logic                         start,
    output logic                         done,
    input  logic [2:0]                   result_index,
    output logic signed [W_OUT-1:0]      result_i,
    output logic signed [W_OUT-1:0]      result_q
);

    localparam integer IFFT_SHIFT = 4 + F_WORK - F_OUT;
    localparam integer W_PRODUCT = W_WORK + W_COEF + 1;
    localparam logic signed [W_PRODUCT:0] PRODUCT_BIAS =
        (F_COEF > 0) ? ({{W_PRODUCT{1'b0}}, 1'b1} << (F_COEF-1)) : '0;
    localparam logic signed [W_WORK:0] OUTPUT_BIAS =
        (IFFT_SHIFT > 0) ? ({{W_WORK{1'b0}}, 1'b1} << (IFFT_SHIFT-1)) : '0;

    logic [4:0] op_index;
    logic [3:0] bin_index;
    logic [2:0] swap_index;
    logic spectral_mode, inverse_mode;
    logic load_work, capture_product, write_bin, write_butterfly, swap_work;
    logic mul_start, mul_done;

    logic signed [W_WORK-1:0] work_i [0:15];
    logic signed [W_WORK-1:0] work_q [0:15];
    logic signed [W_COEF-1:0] twiddle_i, twiddle_q, h_i, h_q;
    logic [3:0] table_a, table_b, swap_a, swap_b;
    logic signed [W_WORK-1:0] twiddled_i, twiddled_q;
    logic [3:0] addr_a, addr_b;
    logic signed [W_WORK+W_COEF:0] mul_p_i, mul_p_q;
    logic signed [W_WORK-1:0] mul_a_i, mul_a_q;
    logic signed [W_COEF-1:0] mul_b_i, mul_b_q;
    logic signed [W_WORK-1:0] load_work_i, load_work_q;
    logic signed [W_WORK:0] sum_i, diff_i, sum_q, diff_q;
    logic signed [W_PRODUCT:0] rounded_product_i, rounded_product_q;
    logic signed [W_WORK:0] scaled_result_i, scaled_result_q;

    frequency_block_engine_control u_control (
        .clk(clk), .rst(rst), .start(start), .load_en(load_en), .mul_done(mul_done),
        .op_index(op_index), .bin_index(bin_index), .swap_index(swap_index),
        .spectral_mode(spectral_mode), .inverse_mode(inverse_mode),
        .load_work(load_work), .capture_product(capture_product), .write_bin(write_bin),
        .write_butterfly(write_butterfly), .swap_work(swap_work),
        .mul_start(mul_start), .done(done)
    );

    frequency_block_roms #(.W_COEF(W_COEF)) u_roms (
        .op_index(op_index), .bin_index(bin_index), .swap_index(swap_index),
        .table_a(table_a), .table_b(table_b), .twiddle_i(twiddle_i), .twiddle_q(twiddle_q),
        .h_i(h_i), .h_q(h_q), .swap_a(swap_a), .swap_b(swap_b)
    );

    complex_mul_serial #(
        .W_A(W_WORK), .W_B(W_COEF), .W_P(W_WORK+W_COEF+1)
    ) u_complex_mul_serial (
        .clk(clk), .rst(rst), .start(mul_start),
        .a_i(mul_a_i), .a_q(mul_a_q), .b_i(mul_b_i), .b_q(mul_b_q),
        .p_i(mul_p_i), .p_q(mul_p_q), .done(mul_done)
    );

    function automatic signed [W_WORK-1:0] input_to_work(
        input signed [W_IN-1:0] sample
    );
        logic signed [W_WORK-1:0] extended_sample;
        begin
            extended_sample = sample;
            input_to_work = extended_sample <<< (F_WORK-F_IN);
        end
    endfunction

    function automatic [3:0] bitrev4(input [3:0] value);
        begin bitrev4 = {value[0], value[1], value[2], value[3]}; end
    endfunction

    assign load_work_i = input_to_work(load_i);
    assign load_work_q = input_to_work(load_q);
    assign addr_a = spectral_mode ? bin_index : table_a;
    assign addr_b = spectral_mode ? bin_index : table_b;
    assign mul_a_i = work_i[addr_b];
    assign mul_a_q = work_q[addr_b];
    assign mul_b_i = spectral_mode ? h_i : twiddle_i;
    assign mul_b_q = spectral_mode ? h_q : (inverse_mode ? -twiddle_q : twiddle_q);
    assign sum_i = $signed({work_i[addr_a][W_WORK-1], work_i[addr_a]}) +
                   $signed({twiddled_i[W_WORK-1], twiddled_i});
    assign diff_i = $signed({work_i[addr_a][W_WORK-1], work_i[addr_a]}) -
                    $signed({twiddled_i[W_WORK-1], twiddled_i});
    assign sum_q = $signed({work_q[addr_a][W_WORK-1], work_q[addr_a]}) +
                   $signed({twiddled_q[W_WORK-1], twiddled_q});
    assign diff_q = $signed({work_q[addr_a][W_WORK-1], work_q[addr_a]}) -
                    $signed({twiddled_q[W_WORK-1], twiddled_q});

    // A04: half-up rounding uses a guard bit before adding the bias.
    assign rounded_product_i = ($signed({mul_p_i[W_PRODUCT-1], mul_p_i}) + PRODUCT_BIAS) >>> F_COEF;
    assign rounded_product_q = ($signed({mul_p_q[W_PRODUCT-1], mul_p_q}) + PRODUCT_BIAS) >>> F_COEF;
    assign scaled_result_i = ($signed({work_i[8+result_index][W_WORK-1], work_i[8+result_index]}) + OUTPUT_BIAS) >>> IFFT_SHIFT;
    assign scaled_result_q = ($signed({work_q[8+result_index][W_WORK-1], work_q[8+result_index]}) + OUTPUT_BIAS) >>> IFFT_SHIFT;
    assign result_i = scaled_result_i;
    assign result_q = scaled_result_q;

    integer n;
    always_ff @(posedge clk) begin
        if (rst) begin
            twiddled_i <= 0;
            twiddled_q <= 0;
            for (n=0; n<16; n=n+1) begin
                work_i[n] <= 0;
                work_q[n] <= 0;
            end
        end else begin
            if (load_work) begin
                work_i[bitrev4(load_index)] <= load_work_i;
                work_q[bitrev4(load_index)] <= load_work_q;
            end
            if (capture_product) begin
                twiddled_i <= rounded_product_i;
                twiddled_q <= rounded_product_q;
            end
            if (write_bin) begin
                work_i[bin_index] <= rounded_product_i;
                work_q[bin_index] <= rounded_product_q;
            end
            if (write_butterfly) begin
                work_i[addr_a] <= sum_i[W_WORK-1:0];
                work_q[addr_a] <= sum_q[W_WORK-1:0];
                work_i[addr_b] <= diff_i[W_WORK-1:0];
                work_q[addr_b] <= diff_q[W_WORK-1:0];
            end
            if (swap_work) begin
                work_i[swap_a] <= work_i[swap_b];
                work_q[swap_a] <= work_q[swap_b];
                work_i[swap_b] <= work_i[swap_a];
                work_q[swap_b] <= work_q[swap_a];
            end
        end
    end

`ifndef SYNTHESIS
    initial begin
        if ((F_COEF != 8) || (W_COEF < 10))
            $fatal(1, "frequency_block_engine constants require F_COEF=8 and W_COEF>=10");
        if (IFFT_SHIFT < 0)
            $fatal(1, "frequency_block_engine requires 4+F_WORK-F_OUT >= 0");
        if ((F_IN < 0) || (F_WORK < F_IN))
            $fatal(1, "frequency_block_engine requires F_WORK>=F_IN>=0");
        if (W_IN <= F_IN || W_WORK < W_IN+F_WORK-F_IN || W_OUT <= F_OUT || F_OUT < 0)
            $fatal(1, "frequency_block_engine requires signed formats and enough width for input alignment");
    end

    always @(posedge clk) begin
        if (!rst) begin
            if ((capture_product || write_bin) &&
                (rounded_product_i != $signed(rounded_product_i[W_WORK-1:0]) ||
                 rounded_product_q != $signed(rounded_product_q[W_WORK-1:0])))
                $fatal(1, "frequency_block_engine: product overflows work");
            if (write_butterfly &&
                (sum_i[W_WORK] != sum_i[W_WORK-1] || diff_i[W_WORK] != diff_i[W_WORK-1] ||
                 sum_q[W_WORK] != sum_q[W_WORK-1] || diff_q[W_WORK] != diff_q[W_WORK-1]))
                $fatal(1, "frequency_block_engine: butterfly overflows work");
            if (done && (scaled_result_i != $signed(result_i) || scaled_result_q != $signed(result_q)))
                $fatal(1, "frequency_block_engine: result overflows output");
        end
    end
`endif
endmodule
