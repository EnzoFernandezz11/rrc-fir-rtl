`timescale 1ns/1ps

module complex_mul_serial_control (
    input  logic       clk,
    input  logic       rst,
    input  logic       start,
    output logic       load_operands,
    output logic       product_en,
    output logic [1:0] product_index,
    output logic       combine_result,
    output logic       sel_a_q,
    output logic       sel_b_q,
    output logic       done
);

    typedef enum logic [2:0] {
        IDLE,
        MUL_II,
        MUL_QQ,
        MUL_IQ,
        MUL_QI,
        COMBINE,
        DONE
    } state_t;

    state_t state;

    always_comb begin
        load_operands = 1'b0;
        product_en = 1'b0;
        product_index = 2'd0;
        combine_result = 1'b0;
        sel_a_q = 1'b0;
        sel_b_q = 1'b0;

        case (state)
            IDLE: load_operands = start;
            MUL_II: begin
                product_en = 1'b1;
            end
            MUL_QQ: begin
                product_en = 1'b1;
                product_index = 2'd1;
                sel_a_q = 1'b1;
                sel_b_q = 1'b1;
            end
            MUL_IQ: begin
                product_en = 1'b1;
                product_index = 2'd2;
                sel_b_q = 1'b1;
            end
            MUL_QI: begin
                product_en = 1'b1;
                product_index = 2'd3;
                sel_a_q = 1'b1;
            end
            COMBINE: combine_result = 1'b1;
            default: begin end
        endcase
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            state <= IDLE;
            done <= 1'b0;
        end else begin
            done <= 1'b0;
            case (state)
                IDLE: if (start) state <= MUL_II;
                MUL_II: state <= MUL_QQ;
                MUL_QQ: state <= MUL_IQ;
                MUL_IQ: state <= MUL_QI;
                MUL_QI: state <= COMBINE;
                COMBINE: begin
                    state <= DONE;
                    done <= 1'b1;
                end
                DONE: state <= IDLE;
                default: state <= IDLE;
            endcase
        end
    end

endmodule
