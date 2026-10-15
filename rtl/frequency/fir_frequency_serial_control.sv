`timescale 1ns/1ps

module fir_frequency_serial_control (
    input  logic       clk,
    input  logic       rst,
    input  logic       in_valid,
    input  logic       in_last,
    output logic       in_ready,
    input  logic       out_ready,
    output logic       out_valid,
    output logic       out_last,
    input  logic       engine_done,
    output logic       history_copy_en,
    output logic [2:0] history_copy_index,
    output logic       history_write_en,
    output logic [2:0] history_write_index,
    output logic       pad_en,
    output logic [2:0] pad_index,
    output logic       history_clear,
    output logic       engine_start,
    output logic [2:0] engine_result_index
);

    localparam [2:0] COPY_HISTORY = 3'd0;
    localparam [2:0] CAPTURE      = 3'd1;
    localparam [2:0] PAD          = 3'd2;
    localparam [2:0] START        = 3'd3;
    localparam [2:0] COMPUTE      = 3'd4;
    localparam [2:0] EMIT         = 3'd5;

    logic [2:0] state;
    logic [2:0] copy_index;
    logic [2:0] sample_count;
    logic [3:0] fill_index;
    logic [3:0] block_count;
    logic [2:0] emit_index;
    logic       block_last;

    assign in_ready = !rst && (state == CAPTURE);
    assign out_valid = !rst && (state == EMIT);
    assign out_last = out_valid && block_last &&
                      ({1'b0, emit_index} + 4'd1 == block_count);

    assign history_copy_en = !rst && (state == COPY_HISTORY);
    assign history_copy_index = copy_index;
    assign history_write_en = !rst && (state == CAPTURE) && in_valid && in_ready;
    assign history_write_index = sample_count;
    assign pad_en = !rst && (state == PAD);
    assign pad_index = fill_index[2:0];
    assign history_clear = !rst && out_valid && out_ready && out_last;
    assign engine_start = !rst && (state == START);
    assign engine_result_index = emit_index;

    always_ff @(posedge clk) begin
        if (rst) begin
            state <= COPY_HISTORY;
            copy_index <= 3'd0;
            sample_count <= 3'd0;
            fill_index <= 4'd0;
            block_count <= 4'd0;
            emit_index <= 3'd0;
            block_last <= 1'b0;
        end else begin
            case (state)
                COPY_HISTORY: begin
                    if (copy_index == 3'd7) begin
                        copy_index <= 3'd0;
                        sample_count <= 3'd0;
                        state <= CAPTURE;
                    end else begin
                        copy_index <= copy_index + 3'd1;
                    end
                end

                CAPTURE: begin
                    if (history_write_en) begin
                        block_last <= in_last;
                        if (in_last) begin
                            block_count <= {1'b0, sample_count} + 4'd1;
                            emit_index <= 3'd0;
                            if (sample_count == 3'd7) begin
                                state <= START;
                            end else begin
                                fill_index <= {1'b0, sample_count} + 4'd1;
                                state <= PAD;
                            end
                        end else if (sample_count == 3'd7) begin
                            block_count <= 4'd8;
                            emit_index <= 3'd0;
                            state <= START;
                        end else begin
                            sample_count <= sample_count + 3'd1;
                        end
                    end
                end

                PAD: begin
                    if (fill_index == 4'd7) begin
                        fill_index <= 4'd0;
                        state <= START;
                    end else begin
                        fill_index <= fill_index + 4'd1;
                    end
                end

                START: begin
                    state <= COMPUTE;
                end

                COMPUTE: begin
                    if (engine_done) begin
                        emit_index <= 3'd0;
                        state <= EMIT;
                    end
                end

                EMIT: begin
                    if (out_valid && out_ready) begin
                        if ({1'b0, emit_index} + 4'd1 == block_count) begin
                            emit_index <= 3'd0;
                            copy_index <= 3'd0;
                            state <= COPY_HISTORY;
                        end else begin
                            emit_index <= emit_index + 3'd1;
                        end
                    end
                end

                default: state <= COPY_HISTORY;
            endcase
        end
    end

endmodule
