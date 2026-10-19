`timescale 1ns/1ps

// Banco PPA de B02, copia del de C02 (tb_fir_frequency_ppa): el mismo estímulo
// por puertos se utiliza con RTL y netlist temporal de Vivado.
module tb_fir_time_ppa;
    localparam integer SAMPLES = 2048;
    // B01: 1 de aceptación + 8 de MAC + 1 de entrega; el "bloque" es una muestra.
    localparam integer LATENCY = 9, INTERVAL = 10;
    real period_ns = 100;
    reg clk = 0;
    initial begin
        if ($value$plusargs("PERIOD_NS=%f", period_ns)) begin
            if (!(period_ns > 0)) $fatal(1, "PERIOD_NS debe ser positivo");
        end
        forever #(period_ns/2.0) clk = ~clk;
    end
    reg rst = 1;
    reg signed [1:0] in_i = 0, in_q = 0;
    reg in_valid = 0, in_last = 0;
    wire in_ready;
    wire signed [8:0] out_i, out_q;
    wire out_valid, out_last;
    reg out_ready = 1;
    reg activity_window = 0;
    reg benchmark_done = 0;
    reg benchmark_pass = 0;

    fir_time_serial dut (
        .clk(clk), .rst(rst), .in_i(in_i), .in_q(in_q),
        .in_valid(in_valid), .in_ready(in_ready), .in_last(in_last),
        .out_i(out_i), .out_q(out_q), .out_valid(out_valid),
        .out_ready(out_ready), .out_last(out_last)
    );

    integer xi [0:SAMPLES-1], xq [0:SAMPLES-1];
    integer yi [0:SAMPLES-1], yq [0:SAMPLES-1];
    integer accepted_at [0:SAMPLES-1];
    integer count, fd, rc, k;
    integer sent = 0, received = 0, cycles = 0;
    integer first_input = 0, first_output = 0, previous_output = 0;
    integer active_cycles, guard;
    integer timing_mode;
    string vectors_path, metrics_path, vcd_path, extra;
    reg dump_enabled = 0;
    real throughput;

    initial begin
        if (!$value$plusargs("VECTORS=%s", vectors_path))
            $fatal(1, "Falta +VECTORS=archivo");
        timing_mode = $test$plusargs("TIMING");
        rc = $value$plusargs("METRICS=%s", metrics_path);
        fd = $fopen(vectors_path, "r");
        if (!fd) $fatal(1, "No se pudo abrir %s", vectors_path);
        rc = $fscanf(fd, "%d", count);
        if (rc != 1 || count != SAMPLES) $fatal(1, "Se requieren %0d muestras", SAMPLES);
        for (k = 0; k < SAMPLES; k = k + 1) begin
            rc = $fscanf(fd, "%d %d %d %d", xi[k], xq[k], yi[k], yq[k]);
            if (rc != 4 || xi[k] < -1 || xi[k] > 1 || xq[k] < -1 || xq[k] > 1 ||
                yi[k] < -256 || yi[k] > 255 || yq[k] < -256 || yq[k] > 255)
                $fatal(1, "Vector invalido en muestra %0d", k);
        end
        rc = $fscanf(fd, "%s", extra);
        if (rc == 1) $fatal(1, "Contenido extra en vectores");
        $fclose(fd);
        if ($value$plusargs("VCD=%s", vcd_path)) begin
            $dumpfile(vcd_path);
            $dumpvars(0, dut);
            $dumpvars(0, activity_window);
            dump_enabled = 1;
        end

        repeat (10) @(posedge clk);
        @(negedge clk);
        rst = 0;
        activity_window = 1;
        in_valid = 1;
        in_i = xi[0]; in_q = xq[0];
        while (received < SAMPLES) begin
            // Valores previos al flanco: son los que acepta el protocolo, incluso con SDF.
            @(posedge clk);
            cycles = cycles + 1;
            if (in_ready !== 1'b0 && in_ready !== 1'b1)
                $fatal(1, "in_ready desconocido en ciclo %0d", cycles);
            if (out_valid !== 1'b0 && out_valid !== 1'b1)
                $fatal(1, "out_valid desconocido en ciclo %0d", cycles);
            if (in_valid && in_ready) begin
                if (sent >= SAMPLES) $fatal(1, "Entrada extra");
                accepted_at[sent] = cycles;
                if (sent == 0) first_input = cycles;
                sent = sent + 1;
            end
            if (out_valid && out_ready) begin
                if (received >= sent) $fatal(1, "Salida sin entrada");
                if (out_i !== yi[received][8:0] || out_q !== yq[received][8:0])
                    $fatal(1, "Muestra %0d: recibido (%0d,%0d), esperado (%0d,%0d)",
                           received, $signed(out_i), $signed(out_q), yi[received], yq[received]);
                if (out_last !== (received == SAMPLES-1))
                    $fatal(1, "out_last incorrecto en muestra %0d", received);
                if (cycles - accepted_at[received] != LATENCY)
                    $fatal(1, "Latencia distinta de %0d en muestra %0d", LATENCY, received);
                if (received == 0) first_output = cycles;
                if (received > 0 && cycles - previous_output != INTERVAL)
                    $fatal(1, "Intervalo distinto de %0d en muestra %0d", INTERVAL, received);
                previous_output = cycles;
                received = received + 1;
            end
            if (cycles > 160000) $fatal(1, "Timeout benchmark PPA");
            @(negedge clk);
            if (dump_enabled && received >= 32) begin
                $dumpoff;
                dump_enabled = 0;
            end
            in_valid = sent < SAMPLES;
            in_last = sent == SAMPLES-1;
            if (sent < SAMPLES) begin in_i = xi[sent]; in_q = xq[sent]; end
        end
        activity_window = 0;
        active_cycles = cycles;
        // La última salida llega LATENCY ciclos después de aceptar x[SAMPLES-1].
        if (sent != SAMPLES || active_cycles != (SAMPLES-1)*INTERVAL + LATENCY + 1)
            $fatal(1, "Conteo final incorrecto: entradas=%0d ciclos=%0d", sent, active_cycles);
        in_valid = 0; in_last = 0; in_i = 0; in_q = 0;
        for (guard = 0; guard < 12; guard = guard + 1) begin
            @(posedge clk);
            if (out_valid !== 1'b0) $fatal(1, "Salida extra tras completar la trama");
            @(negedge clk);
        end
        throughput = SAMPLES * 1.0e9 / (active_cycles * period_ns);
        if (metrics_path != "") begin
            fd = $fopen(metrics_path, "w");
            if (!fd) $fatal(1, "No se pudo abrir %s", metrics_path);
            $fdisplay(fd, "{");
            $fdisplay(fd, "  \"passed\": true,");
            $fdisplay(fd, "  \"timing_simulation\": %s,", timing_mode ? "true" : "false");
            $fdisplay(fd, "  \"seed\": 1, \"symbols\": 1024, \"samples_per_symbol\": 2,");
            $fdisplay(fd, "  \"input_samples\": %0d, \"output_samples\": %0d,", sent, received);
            $fdisplay(fd, "  \"clock_period_ns\": %0.3f, \"active_cycles\": %0d,", period_ns, active_cycles);
            $fdisplay(fd, "  \"activity_start_ns\": %0.3f, \"activity_duration_ns\": %0.3f,", 10*period_ns, active_cycles*period_ns);
            $fdisplay(fd, "  \"latency_cycles\": %0d, \"block_cycles\": %0d, \"blocks\": %0d,", first_output-first_input, INTERVAL, SAMPLES);
            $fdisplay(fd, "  \"throughput_samples_per_second\": %.9f", throughput);
            $fdisplay(fd, "}");
            $fclose(fd);
        end
        benchmark_pass = 1;
        benchmark_done = 1;
        $display("PASS PPA: %0d muestras, L=%0d, II=%0d, %0d ciclos, %.3f muestras/s",
                 received, first_output-first_input, INTERVAL, active_cycles, throughput);
        #100;
        $finish;
    end
endmodule
