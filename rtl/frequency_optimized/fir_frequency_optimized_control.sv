`timescale 1ns/1ps

module fir_frequency_optimized_control (
    input  logic clk, rst,
    input  logic in_valid, in_last,
    output logic in_ready,
    input  logic out_ready,
    output logic out_valid, out_last,
    output logic capture_en, capture_bank,
    output logic [2:0] capture_index,
    output logic history_clear,
    output logic fft_in_valid, fft_source,
    input  logic fft_out_valid,
    output logic fft_capture, fft_dest,
    output logic spectral_in_valid, spectral_source,
    input  logic spectral_out_valid,
    output logic spectral_capture, spectral_dest,
    output logic ifft_in_valid, ifft_source,
    input  logic ifft_out_valid,
    output logic useful_capture, output_capture, output_dest,
    output logic [3:0] output_count,
    output logic emit_bank,
    output logic [2:0] emit_index,
    output logic [7:0] emit_select
);
    logic [1:0] window_busy, window_complete;
    logic [1:0] x_busy, x_complete, y_busy, y_complete;
    logic [1:0] output_busy, output_complete;
    logic window_write, window_read, x_write, x_read;
    logic y_write, y_read, output_write;
    logic frame_wait;
    logic [3:0] window_p [0:1], x_p [0:1], y_p [0:1], output_p [0:1];
    logic [1:0] window_last, x_last, y_last, output_last;

    // Tokens are {last, useful sample count, reserved destination}.
    logic [5:0] fft_token [0:5];
    logic [5:0] spectral_token [0:1];
    logic [5:0] ifft_token [0:5];
    logic [5:0] useful_token;
    logic fft_launch, spectral_launch, ifft_launch, emit_finish;

    assign in_ready = !rst && !frame_wait &&
                      ((capture_index != 0) || !window_busy[window_write]);
    assign capture_en = in_valid && in_ready;
    assign capture_bank = window_write;
    // Keep output masking on a short, dedicated reset branch; internal state still uses rst.
    (* keep = "true" *) wire rst_output_n = ~rst;
    assign out_valid = rst_output_n && output_complete[emit_bank];
    assign emit_finish = out_valid && out_ready &&
                         ({1'b0, emit_index} + 4'd1 == output_p[emit_bank]);
    assign out_last = rst_output_n && output_complete[emit_bank] && output_last[emit_bank] &&
                      ({1'b0, emit_index} + 4'd1 == output_p[emit_bank]);
    assign history_clear = out_valid && out_ready && out_last;

    assign fft_launch = !rst && window_complete[window_read] && !x_busy[x_write];
    assign spectral_launch = !rst && x_complete[x_read] && !y_busy[y_write];
    assign ifft_launch = !rst && y_complete[y_read] && !output_busy[output_write];
    assign fft_capture = !rst && fft_out_valid;
    assign fft_dest = fft_token[5][0];
    assign spectral_capture = !rst && spectral_out_valid;
    assign spectral_dest = spectral_token[1][0];
    assign useful_capture = !rst && ifft_out_valid;
    assign output_dest = useful_token[0];
    assign output_count = useful_token[4:1];

    integer k;
    always_ff @(posedge clk) begin
        if (rst) begin
            window_busy <= 0;
            window_complete <= 0;
            x_busy <= 0;
            x_complete <= 0;
            y_busy <= 0;
            y_complete <= 0;
            output_busy <= 0;
            output_complete <= 0;
            window_write <= 0;
            window_read <= 0;
            x_write <= 0;
            x_read <= 0;
            y_write <= 0;
            y_read <= 0;
            output_write <= 0;
            emit_bank <= 0;
            emit_index <= 0;
            emit_select <= 8'b0000_0001;
            capture_index <= 0;
            frame_wait <= 0;
            window_last <= 0;
            x_last <= 0;
            y_last <= 0;
            output_last <= 0;
            fft_in_valid <= 0;
            spectral_in_valid <= 0;
            ifft_in_valid <= 0;
            output_capture <= 0;
            fft_source <= 0;
            spectral_source <= 0;
            ifft_source <= 0;
            useful_token <= 0;
            for (k = 0; k < 2; k = k + 1) begin
                window_p[k] <= 0;
                x_p[k] <= 0;
                y_p[k] <= 0;
                output_p[k] <= 0;
                spectral_token[k] <= 0;
            end
            for (k = 0; k < 6; k = k + 1) begin
                fft_token[k] <= 0;
                ifft_token[k] <= 0;
            end
        end else begin
            fft_in_valid <= fft_launch;
            spectral_in_valid <= spectral_launch;
            ifft_in_valid <= ifft_launch;
            output_capture <= useful_capture;
            for (k = 1; k < 6; k = k + 1) begin
                fft_token[k] <= fft_token[k-1];
                ifft_token[k] <= ifft_token[k-1];
            end
            spectral_token[1] <= spectral_token[0];

            if (capture_en) begin
                window_busy[window_write] <= 1;
                if (in_last || capture_index == 3'd7) begin
                    window_complete[window_write] <= 1;
                    window_p[window_write] <= {1'b0, capture_index} + 4'd1;
                    window_last[window_write] <= in_last;
                    window_write <= !window_write;
                    capture_index <= 0;
                end else begin
                    capture_index <= capture_index + 3'd1;
                end
                if (in_last) frame_wait <= 1;
            end
            if (history_clear) frame_wait <= 0;

            if (fft_launch) begin
                fft_source <= window_read;
                fft_token[0] <= {window_last[window_read], window_p[window_read], x_write};
                window_complete[window_read] <= 0;
                window_read <= !window_read;
                x_busy[x_write] <= 1;
                x_write <= !x_write;
            end
            // The registered request consumes its source one edge after launch.
            if (fft_in_valid) window_busy[fft_source] <= 0;
            if (fft_capture) begin
                x_complete[fft_dest] <= 1;
                x_p[fft_dest] <= fft_token[5][4:1];
                x_last[fft_dest] <= fft_token[5][5];
            end

            if (spectral_launch) begin
                spectral_source <= x_read;
                spectral_token[0] <= {x_last[x_read], x_p[x_read], y_write};
                x_complete[x_read] <= 0;
                x_read <= !x_read;
                y_busy[y_write] <= 1;
                y_write <= !y_write;
            end
            if (spectral_in_valid) x_busy[spectral_source] <= 0;
            if (spectral_capture) begin
                y_complete[spectral_dest] <= 1;
                y_p[spectral_dest] <= spectral_token[1][4:1];
                y_last[spectral_dest] <= spectral_token[1][5];
            end

            if (ifft_launch) begin
                ifft_source <= y_read;
                ifft_token[0] <= {y_last[y_read], y_p[y_read], output_write};
                y_complete[y_read] <= 0;
                y_read <= !y_read;
                output_busy[output_write] <= 1;
                output_write <= !output_write;
            end
            if (ifft_in_valid) y_busy[ifft_source] <= 0;
            if (useful_capture) useful_token <= ifft_token[5];
            if (output_capture) begin
                output_complete[output_dest] <= 1;
                output_p[output_dest] <= useful_token[4:1];
                output_last[output_dest] <= useful_token[5];
            end

            if (out_valid && out_ready) begin
                if (emit_finish) begin
                    output_complete[emit_bank] <= 0;
                    output_busy[emit_bank] <= 0;
                    emit_bank <= !emit_bank;
                    emit_index <= 0;
                    emit_select <= 8'b0000_0001;
                end else begin
                    emit_index <= emit_index + 3'd1;
                    emit_select <= {emit_select[6:0], emit_select[7]};
                end
            end
        end
    end

`ifndef SYNTHESIS
    always @(posedge clk) begin
        if (!rst) begin
            if (fft_capture && (!x_busy[fft_dest] || x_complete[fft_dest]))
                $fatal(1, "FFT destination is not exclusively reserved");
            if (spectral_capture && (!y_busy[spectral_dest] || y_complete[spectral_dest]))
                $fatal(1, "Spectral destination is not exclusively reserved");
            if (output_capture && (!output_busy[output_dest] || output_complete[output_dest]))
                $fatal(1, "Output destination is not exclusively reserved");
        end
    end
`endif
endmodule
