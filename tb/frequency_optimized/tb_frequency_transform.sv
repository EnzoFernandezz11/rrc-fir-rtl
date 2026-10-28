`timescale 1ns/1ps

module tb_frequency_transform;
    reg clk = 0, rst = 1, in_valid = 0;
    always #5 clk = ~clk;
    reg [191:0] fi = 0, fq = 0, ii = 0, iq = 0;
    wire [191:0] fo_i, fo_q, io_i, io_q;
    wire fv, iv;
    reg final_valid;
    reg [191:0] final_fi, final_fq, final_ii, final_iq;
    frequency_fft16 fwd(.clk(clk), .rst(rst), .in_valid(in_valid),
        .in_i(fi), .in_q(fq), .out_valid(fv), .out_i(fo_i), .out_q(fo_q));
    frequency_fft16 #(.INVERSE(1)) inv(.clk(clk), .rst(rst), .in_valid(in_valid),
        .in_i(ii), .in_q(iq), .out_valid(iv), .out_i(io_i), .out_q(io_q));
    reg signed [11:0] inputs_i [0:511][0:1][0:15];
    reg signed [11:0] inputs_q [0:511][0:1][0:15];
    reg signed [11:0] expected_i [0:511][0:7][0:15];
    reg signed [11:0] expected_q [0:511][0:7][0:15];
    integer tag [0:5];
    integer send_tag = -1, checked = 0, edge_index;
    always @(posedge clk) begin
        if (rst) begin
            final_valid <= 0;
            for (edge_index=0; edge_index<6; edge_index=edge_index+1)
                tag[edge_index] <= -1;
        end else begin
            tag[0] <= in_valid ? send_tag : -1;
            for (edge_index=1; edge_index<6; edge_index=edge_index+1)
                tag[edge_index] <= tag[edge_index-1];
            final_valid <= fv;
            if (fv) begin
                final_fi <= fo_i; final_fq <= fo_q;
                final_ii <= io_i; final_iq <= io_q;
            end
        end
    end

    integer stage, bin, tag_index, transaction;
    always @(negedge clk) begin
        if (!rst) begin
            for (stage=0; stage<4; stage=stage+1) begin
                case(stage)
                    0:tag_index=0; 1:tag_index=1; 2:tag_index=3; 3:tag_index=4;
                endcase
                transaction = tag[tag_index];
                if (fwd.stage_valid[stage+1] !== (transaction >= 0) ||
                    inv.stage_valid[stage+1] !== (transaction >= 0))
                    $fatal(1, "Transform stage valid/latency mismatch stage=%0d", stage);
                if (transaction >= 0) begin
                    for (bin=0; bin<16; bin=bin+1) begin
                        if ($signed(fwd.stage_i[stage+1][12*bin +: 12]) !== expected_i[transaction][stage][bin] ||
                            $signed(fwd.stage_q[stage+1][12*bin +: 12]) !== expected_q[transaction][stage][bin])
                            $fatal(1, "FFT checkpoint transaction=%0d stage=%0d bin=%0d", transaction, stage, bin);
                        if ($signed(inv.stage_i[stage+1][12*bin +: 12]) !== expected_i[transaction][stage+4][bin] ||
                            $signed(inv.stage_q[stage+1][12*bin +: 12]) !== expected_q[transaction][stage+4][bin])
                            $fatal(1, "IFFT checkpoint transaction=%0d stage=%0d bin=%0d", transaction, stage, bin);
                    end
                end
            end
            if (final_valid !== (tag[5] >= 0))
                $fatal(1, "Final destination must be capture six");
            if (final_valid) begin
                for (bin=0; bin<16; bin=bin+1) begin
                    if ($signed(final_fi[12*bin +: 12]) !== expected_i[tag[5]][3][bin] ||
                        $signed(final_fq[12*bin +: 12]) !== expected_q[tag[5]][3][bin] ||
                        $signed(final_ii[12*bin +: 12]) !== expected_i[tag[5]][7][bin] ||
                        $signed(final_iq[12*bin +: 12]) !== expected_q[tag[5]][7][bin])
                        $fatal(1, "Final bank data mismatch");
                end
                checked = checked+1;
            end
        end
    end

    integer fd, count, status, n, s, k, real_value, imag_value, mode=0, cycle=0;
    reg [4095:0] vector_file;
    initial begin
        if (!$value$plusargs("vectors=%s", vector_file)) $fatal(1, "Missing vectors");
        status = $value$plusargs("mode=%d", mode);
        fd = $fopen(vector_file, "r");
        status = $fscanf(fd, "%d", count);
        if (status != 1 || count > 512) $fatal(1, "Invalid count");
        for (n=0; n<count; n=n+1) begin
            for (s=0; s<2; s=s+1)
                for (k=0; k<16; k=k+1) begin
                    status = $fscanf(fd, "%d %d", real_value, imag_value);
                    if (status != 2) $fatal(1, "Invalid input");
                    inputs_i[n][s][k] = real_value; inputs_q[n][s][k] = imag_value;
                end
            for (s=0; s<8; s=s+1)
                for (k=0; k<16; k=k+1) begin
                    status = $fscanf(fd, "%d %d", real_value, imag_value);
                    if (status != 2) $fatal(1, "Invalid checkpoint");
                    expected_i[n][s][k] = real_value; expected_q[n][s][k] = imag_value;
                end
        end
        $fclose(fd);
        repeat(2) @(negedge clk);
        n=0;
        while(n<count) begin
            // Drive after the scoreboard samples the previous cycle.
            #1;
            rst = mode == 2 && (cycle == 19 || cycle == 55 || cycle == 88 || cycle == 100);
            in_valid = !rst && (mode == 0 || cycle%9 != 3);
            send_tag = n;
            for(k=0; k<16; k=k+1) begin
                fi[12*k +: 12] = inputs_i[n][0][k]; fq[12*k +: 12] = inputs_q[n][0][k];
                ii[12*k +: 12] = inputs_i[n][1][k]; iq[12*k +: 12] = inputs_q[n][1][k];
            end
            if(in_valid) n=n+1;
            cycle=cycle+1;
            @(negedge clk);
        end
        #1; in_valid=0; rst=0;
        repeat(8) @(negedge clk);
        #1;
        if (mode != 2 && checked != count) $fatal(1, "Missing transform results");
        if (checked < count-24) $fatal(1, "Too many reset losses");
        $display("PASS transforms: %0d destination captures, mode=%0d, 8 stage checkpoints", checked, mode);
        $finish;
    end
endmodule
