`timescale 1ns/1ps

module fir_frequency_serial #(
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
    input  logic signed [W_IN-1:0]       in_i,
    input  logic signed [W_IN-1:0]       in_q,
    input  logic                         in_valid,
    output logic                         in_ready,
    input  logic                         in_last,
    output logic signed [W_OUT-1:0]      out_i,
    output logic signed [W_OUT-1:0]      out_q,
    output logic                         out_valid,
    input  logic                         out_ready,
    output logic                         out_last
);

    logic       history_copy_en;
    logic [2:0] history_copy_index;
    logic       history_write_en;
    logic [2:0] history_write_index;
    logic       pad_en;
    logic [2:0] pad_index;
    logic       history_clear;

    logic       engine_load_en;
    logic [3:0] engine_load_index;
    logic signed [W_IN-1:0] engine_load_i;
    logic signed [W_IN-1:0] engine_load_q;
    logic       engine_start;
    logic       engine_done;
    logic [2:0] engine_result_index;
    logic signed [W_OUT-1:0] engine_result_i;
    logic signed [W_OUT-1:0] engine_result_q;

    logic signed [W_IN-1:0] history_i [0:7];
    logic signed [W_IN-1:0] history_q [0:7];

    assign engine_load_en = history_copy_en || history_write_en || pad_en;
    assign engine_load_index = history_copy_en ? {1'b0, history_copy_index} :
                               history_write_en ? (4'd8 + {1'b0, history_write_index}) :
                               (4'd8 + {1'b0, pad_index});
    assign engine_load_i = history_copy_en ? history_i[history_copy_index] :
                           history_write_en ? in_i : {W_IN{1'b0}};
    assign engine_load_q = history_copy_en ? history_q[history_copy_index] :
                           history_write_en ? in_q : {W_IN{1'b0}};

    assign out_i = engine_result_i;
    assign out_q = engine_result_q;

    fir_frequency_serial_control u_control (
        .clk(clk),
        .rst(rst),
        .in_valid(in_valid),
        .in_last(in_last),
        .in_ready(in_ready),
        .out_ready(out_ready),
        .out_valid(out_valid),
        .out_last(out_last),
        .engine_done(engine_done),
        .history_copy_en(history_copy_en),
        .history_copy_index(history_copy_index),
        .history_write_en(history_write_en),
        .history_write_index(history_write_index),
        .pad_en(pad_en),
        .pad_index(pad_index),
        .history_clear(history_clear),
        .engine_start(engine_start),
        .engine_result_index(engine_result_index)
    );

    frequency_block_engine #(
        .W_IN(W_IN), .F_IN(F_IN),
        .W_WORK(W_WORK), .F_WORK(F_WORK),
        .W_COEF(W_COEF), .F_COEF(F_COEF),
        .W_OUT(W_OUT), .F_OUT(F_OUT)
    ) u_engine (
        .clk(clk),
        .rst(rst),
        .load_en(engine_load_en),
        .load_index(engine_load_index),
        .load_i(engine_load_i),
        .load_q(engine_load_q),
        .start(engine_start),
        .done(engine_done),
        .result_index(engine_result_index),
        .result_accept(out_valid && out_ready),
        .result_i(engine_result_i),
        .result_q(engine_result_q)
    );

    integer i;
    always_ff @(posedge clk) begin
        if (rst) begin
            for (i = 0; i < 8; i = i + 1) begin
                history_i[i] <= {W_IN{1'b0}};
                history_q[i] <= {W_IN{1'b0}};
            end
        end else if (history_clear) begin
            for (i = 0; i < 8; i = i + 1) begin
                history_i[i] <= {W_IN{1'b0}};
                history_q[i] <= {W_IN{1'b0}};
            end
        end else if (history_write_en) begin
            history_i[history_write_index] <= in_i;
            history_q[history_write_index] <= in_q;
        end
    end

endmodule
