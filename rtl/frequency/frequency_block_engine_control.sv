`timescale 1ns/1ps

module frequency_block_engine_control (
    input  logic       clk,
    input  logic       rst,
    input  logic       start,
    input  logic       load_en,
    input  logic       mul_done,
    output logic [4:0] op_index,
    output logic [3:0] bin_index,
    output logic [2:0] swap_index,
    output logic       spectral_mode,
    output logic       inverse_mode,
    output logic       load_work,
    output logic       capture_product,
    output logic       write_bin,
    output logic       write_butterfly,
    output logic       swap_work,
    output logic       mul_start,
    output logic       done
);
    localparam logic [2:0] PH_FFT  = 3'd0,
                           PH_MUL  = 3'd1,
                           PH_IFFT = 3'd2;
    localparam logic [2:0] ST_IDLE    = 3'd0,
                           ST_LAUNCH  = 3'd1,
                           ST_WAIT    = 3'd2,
                           ST_WRITE   = 3'd3,
                           ST_REORDER = 3'd4;

    logic [2:0] state, phase;

    always_comb begin
        spectral_mode = (phase == PH_MUL);
        inverse_mode = (phase == PH_IFFT);
        load_work = (state == ST_IDLE) && load_en;
        mul_start = (state == ST_LAUNCH) || ((state == ST_IDLE) && start);
        capture_product = (state == ST_WAIT) && mul_done && !spectral_mode;
        write_bin = (state == ST_WAIT) && mul_done && spectral_mode;
        write_butterfly = (state == ST_WRITE);
        swap_work = (state == ST_REORDER);
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            state <= ST_IDLE;
            phase <= PH_FFT;
            op_index <= 0;
            bin_index <= 0;
            swap_index <= 0;
            done <= 1'b0;
        end else begin
            done <= 1'b0;
            case (state)
                ST_IDLE: if (start) begin
                    phase <= PH_FFT;
                    op_index <= 0;
                    bin_index <= 0;
                    state <= ST_WAIT;
                end
                ST_LAUNCH: state <= ST_WAIT;
                ST_WAIT: if (mul_done) begin
                    if (spectral_mode) begin
                        if (bin_index == 15) begin
                            phase <= PH_IFFT;
                            op_index <= 0;
                            swap_index <= 0;
                            state <= ST_REORDER;
                        end else begin
                            bin_index <= bin_index + 1'b1;
                            state <= ST_LAUNCH;
                        end
                    end else begin
                        state <= ST_WRITE;
                    end
                end
                ST_WRITE: begin
                    if (op_index == 31) begin
                        if (!inverse_mode) begin
                            phase <= PH_MUL;
                            bin_index <= 0;
                            state <= ST_LAUNCH;
                        end else begin
                            done <= 1'b1;
                            phase <= PH_FFT;
                            op_index <= 0;
                            state <= ST_IDLE;
                        end
                    end else begin
                        op_index <= op_index + 1'b1;
                        state <= ST_LAUNCH;
                    end
                end
                ST_REORDER: begin
                    if (swap_index == 5) begin
                        op_index <= 0;
                        state <= ST_LAUNCH;
                    end else begin
                        swap_index <= swap_index + 1'b1;
                    end
                end
                default: state <= ST_IDLE;
            endcase
        end
    end
endmodule
