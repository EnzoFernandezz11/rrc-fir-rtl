`timescale 1ns/1ps

module fir_frequency_optimized (
    input  logic clk, rst,
    input  logic signed [1:0] in_i, in_q,
    input  logic in_valid,
    output logic in_ready,
    input  logic in_last,
    output logic signed [8:0] out_i, out_q,
    output logic out_valid,
    input  logic out_ready,
    output logic out_last
);
    logic capture_en, capture_bank, history_clear;
    logic [2:0] capture_index, emit_index;
    logic [7:0] emit_select;
    logic fft_in_valid, fft_source, fft_out_valid, fft_capture, fft_dest;
    logic spectral_in_valid, spectral_source, spectral_out_valid, spectral_capture, spectral_dest;
    logic ifft_in_valid, ifft_source, ifft_out_valid, useful_capture;
    logic output_capture, output_dest, emit_bank;
    logic [3:0] output_count;
    logic signed [1:0] history_i [0:7], history_q [0:7];
    logic [31:0] window_i [0:1], window_q [0:1];
    logic [191:0] x_i [0:1], x_q [0:1], y_i [0:1], y_q [0:1];
    logic [71:0] output_i [0:1], output_q [0:1];
    logic [191:0] fft_input_i, fft_input_q, fft_result_i, fft_result_q;
    logic [191:0] spectral_result_i, spectral_result_q, ifft_result_i, ifft_result_q;
    logic [95:0] useful_i, useful_q;
    logic [71:0] scaled_i, scaled_q;

    fir_frequency_optimized_control u_control (
        .clk(clk), .rst(rst),
        .in_valid(in_valid), .in_last(in_last), .in_ready(in_ready),
        .out_ready(out_ready), .out_valid(out_valid), .out_last(out_last),
        .capture_en(capture_en), .capture_bank(capture_bank), .capture_index(capture_index),
        .history_clear(history_clear),
        .fft_in_valid(fft_in_valid), .fft_source(fft_source), .fft_out_valid(fft_out_valid),
        .fft_capture(fft_capture), .fft_dest(fft_dest),
        .spectral_in_valid(spectral_in_valid), .spectral_source(spectral_source),
        .spectral_out_valid(spectral_out_valid), .spectral_capture(spectral_capture),
        .spectral_dest(spectral_dest),
        .ifft_in_valid(ifft_in_valid), .ifft_source(ifft_source), .ifft_out_valid(ifft_out_valid),
        .useful_capture(useful_capture), .output_capture(output_capture), .output_dest(output_dest),
        .output_count(output_count),
        .emit_bank(emit_bank), .emit_index(emit_index), .emit_select(emit_select)
    );

    genvar n;
    generate
        for (n = 0; n < 16; n = n + 1) begin : input_format
            assign fft_input_i[n*12 +: 12] = {{5{window_i[fft_source][n*2+1]}},
                                            window_i[fft_source][n*2 +: 2], 5'b0};
            assign fft_input_q[n*12 +: 12] = {{5{window_q[fft_source][n*2+1]}},
                                            window_q[fft_source][n*2 +: 2], 5'b0};
        end
    endgenerate

    frequency_fft16 #(.INVERSE(0)) u_fft (
        .clk(clk), .rst(rst), .in_valid(fft_in_valid),
        .in_i(fft_input_i), .in_q(fft_input_q),
        .out_valid(fft_out_valid), .out_i(fft_result_i), .out_q(fft_result_q)
    );
    frequency_spectral16 u_spectral (
        .clk(clk), .rst(rst), .in_valid(spectral_in_valid),
        .in_i(x_i[spectral_source]), .in_q(x_q[spectral_source]),
        .out_valid(spectral_out_valid), .out_i(spectral_result_i), .out_q(spectral_result_q)
    );
    frequency_fft16 #(.INVERSE(1)) u_ifft (
        .clk(clk), .rst(rst), .in_valid(ifft_in_valid),
        .in_i(y_i[ifft_source]), .in_q(y_q[ifft_source]),
        .out_valid(ifft_out_valid), .out_i(ifft_result_i), .out_q(ifft_result_q)
    );
    frequency_output_scale u_scale (
        .in_i(useful_i), .in_q(useful_q), .out_i(scaled_i), .out_q(scaled_q)
    );

    frequency_output_select_onehot u_output_select (
        .valid(out_valid), .bank(emit_bank), .select(emit_select),
        .i0(output_i[0]), .i1(output_i[1]), .q0(output_q[0]), .q1(output_q[1]),
        .out_i(out_i), .out_q(out_q)
    );

    integer k;
    always_ff @(posedge clk) begin
        if (rst || history_clear) begin
            for (k = 0; k < 8; k = k + 1) begin
                history_i[k] <= 0;
                history_q[k] <= 0;
            end
        end else if (capture_en) begin
            history_i[capture_index] <= in_i;
            history_q[capture_index] <= in_q;
        end

        if (!rst) begin
            if (capture_en) begin
                for (k = 0; k < 8; k = k + 1) begin
                    if (capture_index == 0) begin
                        window_i[capture_bank][k*2 +: 2] <= history_i[k];
                        window_q[capture_bank][k*2 +: 2] <= history_q[k];
                    end
                    if (k == capture_index) begin
                        window_i[capture_bank][(8+k)*2 +: 2] <= in_i;
                        window_q[capture_bank][(8+k)*2 +: 2] <= in_q;
                    end else if (capture_index == 0) begin
                        // Clear the whole tail when opening a window: partial blocks are ready immediately.
                        window_i[capture_bank][(8+k)*2 +: 2] <= 0;
                        window_q[capture_bank][(8+k)*2 +: 2] <= 0;
                    end
                end
            end
            if (fft_capture) begin
                x_i[fft_dest] <= fft_result_i;
                x_q[fft_dest] <= fft_result_q;
            end
            if (spectral_capture) begin
                y_i[spectral_dest] <= spectral_result_i;
                y_q[spectral_dest] <= spectral_result_q;
            end
            if (useful_capture) begin
                useful_i <= ifft_result_i[191:96];
                useful_q <= ifft_result_q[191:96];
            end
            if (output_capture) begin
                output_i[output_dest] <= scaled_i;
                output_q[output_dest] <= scaled_q;
            end
        end
    end

`ifndef SYNTHESIS
    integer check_index;
    integer check_i, check_q;
    always @(posedge clk) begin
        if (!rst) begin
            if (emit_select !== (8'b1 << emit_index))
                $fatal(1, "One-hot output selector lost sync with emit_index");
            if (capture_en &&
                (((in_i !== -2'sd1) && (in_i !== 2'sd0) && (in_i !== 2'sd1)) ||
                 ((in_q !== -2'sd1) && (in_q !== 2'sd0) && (in_q !== 2'sd1))))
                $fatal(1, "Input is outside the supported {-1,0,1} domain");
            if (output_capture) begin
                for (check_index = 0; check_index < 8; check_index = check_index + 1) begin
                    if (check_index < output_count) begin
                        check_i = ($signed(useful_i[check_index*12 +: 12]) + 32'sd2) >>> 2;
                        check_q = ($signed(useful_q[check_index*12 +: 12]) + 32'sd2) >>> 2;
                        if (check_i < -256 || check_i > 255 || check_q < -256 || check_q > 255)
                            $fatal(1, "Output conversion overflow");
                    end
                end
            end
        end
    end
`endif
endmodule
