`timescale 1ns/1ps

// A04/A05 reference and parser reused from the serial bench; only the driver
// and timing/protocol checks change for overlapping blocks.
module tb_fir_frequency_optimized;
    localparam integer MAX_SAMPLES = 4096;
    localparam integer EXPECTED_LATENCY = 26;
    logic clk = 0;
    always #5 clk = ~clk;
    logic rst = 1;
    logic signed [1:0] in_i = 0, in_q = 0;
    logic in_valid = 0, in_last = 0, in_ready;
    logic signed [8:0] out_i, out_q;
    logic out_valid, out_last, out_ready = 0;
    fir_frequency_optimized dut (.*);

    integer xi [0:MAX_SAMPLES-1], xq [0:MAX_SAMPLES-1];
    longint signed yi [0:MAX_SAMPLES-1], yq [0:MAX_SAMPLES-1];
    longint signed wr [0:15], wi [0:15];
    longint signed hr [0:15], hi [0:15];
    longint signed twr [0:7], twi [0:7], taps [0:7];
    integer vectors_fd;
    string frame_name = "local";
    bit use_model_expected = 0;
    integer cycles = 0, frames = 0;
    integer continuous_frames = 0, long_stall_frames = 0;
    logic stalled = 0;
    logic signed [8:0] held_i, held_q;
    logic held_last;
    bit prolonged_stalls = 0;

    always @(posedge clk) begin
        cycles = cycles + 1;
        if (cycles > 2000000) $fatal(1, "Timeout global optimized");
        if (!rst && stalled &&
            (!out_valid || out_i !== held_i || out_q !== held_q || out_last !== held_last))
            $fatal(1, "Salida cambio durante backpressure");
        if (rst && (in_ready || out_valid)) $fatal(1, "Transferencia durante reset");
        if (!rst && (in_ready === 1'bx || out_valid === 1'bx))
            $fatal(1, "Handshake desconocido");
        stalled = !rst && out_valid && !out_ready;
        held_i = out_i; held_q = out_q; held_last = out_last;
    end


    function automatic longint signed round_shift(input longint signed value, input integer shift);
        round_shift = (shift == 0) ? value : (value + (64'sd1 << (shift-1))) >>> shift;
    endfunction

    function automatic integer reverse4(input integer n);
        reverse4 = ((n & 1) << 3) | ((n & 2) << 1) | ((n & 4) >> 1) | ((n & 8) >> 3);
    endfunction

    task automatic load_model_constants;
        integer w_work, f_work, w_coef, f_coef, w_out, f_out, index;
        begin
            vectors_fd = $fopen("build/frequency_serial_vectors.txt", "r");
            if (!vectors_fd) $fatal(1, "Faltan vectores A04: ejecutar make smoke desde la raiz");
            if ($fscanf(vectors_fd, "%d %d %d %d %d %d", w_work, f_work, w_coef, f_coef, w_out, f_out) != 6)
                $fatal(1, "Cabecera de formatos A04 invalida");
            if (w_work != 12 || f_work != 5 || w_coef != 10 ||
                f_coef != 8 || w_out != 9 || f_out != 7)
                $fatal(1, "Los formatos RTL no coinciden con config/project.json y A04");
            for (index=0; index<8; index=index+1)
                if ($fscanf(vectors_fd, "%d", taps[index]) != 1) $fatal(1, "Taps A04 invalidos");
            for (index=0; index<16; index=index+1)
                if ($fscanf(vectors_fd, "%d %d", hr[index], hi[index]) != 2) $fatal(1, "H A04 invalido");
            for (index=0; index<8; index=index+1)
                if ($fscanf(vectors_fd, "%d %d", twr[index], twi[index]) != 2) $fatal(1, "W A04 invalido");
        end
    endtask

    function automatic longint signed checked_work(input longint signed value);
        begin
            if (value < -64'sd2048 || value > 64'sd2047)
                $fatal(1, "Overflow Q7.5 en referencia: %0d", value);
            checked_work = value;
        end
    endfunction

    task automatic transform(input bit inverse);
        integer size, base, j, a, b, k;
        longint signed ar, ai, tr, ti, cr, ci;
        begin
            for (size = 2; size <= 16; size = size * 2)
                for (base = 0; base < 16; base = base + size)
                    for (j = 0; j < size/2; j = j + 1) begin
                        a = base + j;
                        b = a + size/2;
                        k = j * 16 / size;
                        cr = twr[k];
                        ci = inverse ? -twi[k] : twi[k];
                        ar = wr[a]; ai = wi[a];
                        tr = checked_work(round_shift(wr[b]*cr - wi[b]*ci, 8));
                        ti = checked_work(round_shift(wr[b]*ci + wi[b]*cr, 8));
                        wr[a] = checked_work(ar + tr); wi[a] = checked_work(ai + ti);
                        wr[b] = checked_work(ar - tr); wi[b] = checked_work(ai - ti);
                    end
        end
    endtask

    task automatic reference_frame(input integer length);
        integer offset, r, n, k, rev;
        longint signed tr, ti;
        begin
            for (offset = 0; offset < length; offset = offset + 8) begin
                for (r = 0; r < 16; r = r + 1) begin
                    n = offset - 8 + r;
                    rev = reverse4(r);
                    wr[rev] = (n >= 0 && n < length) ? 64'(xi[n]) * 32 : 0;
                    wi[rev] = (n >= 0 && n < length) ? 64'(xq[n]) * 32 : 0;
                end
                transform(0);
                for (k = 0; k < 16; k = k + 1) begin
                    tr = checked_work(round_shift(wr[k]*hr[k] - wi[k]*hi[k], 8));
                    ti = checked_work(round_shift(wr[k]*hi[k] + wi[k]*hr[k], 8));
                    wr[k] = tr; wi[k] = ti;
                end
                for (k = 0; k < 16; k = k + 1) begin
                    rev = reverse4(k);
                    if (rev > k) begin
                        tr = wr[k]; wr[k] = wr[rev]; wr[rev] = tr;
                        ti = wi[k]; wi[k] = wi[rev]; wi[rev] = ti;
                    end
                end
                transform(1);
                for (r = 0; r < 8 && offset+r < length; r = r + 1) begin
                    yi[offset+r] = round_shift(wr[8+r], 2);
                    yq[offset+r] = round_shift(wi[8+r], 2);
                end
            end
        end
    endtask

    task automatic reset_filter;
        begin
            @(negedge clk); rst = 1; in_valid = 0; in_last = 0; out_ready = 0;
            #1;
            if (in_ready || out_valid) $fatal(1, "Reset no inhibe interfaz");
            repeat (2) @(posedge clk);
            @(negedge clk); rst = 0;
            #1;
            if (out_valid) $fatal(1, "Resultado residual tras reset");
        end
    endtask

    task automatic run_frame(input integer length, input bit pauses);
        integer sent, received, local_cycle, first_input, first_output;
        integer accepted_at [0:MAX_SAMPLES-1];
        integer previous_output, previous_block, blocked_inputs, stalled_outputs;
        bit pending;
        begin
            if (!use_model_expected) reference_frame(length);
            sent = 0; received = 0; local_cycle = 0; pending = 0;
            first_input = 0; first_output = 0; previous_output = 0; previous_block = 0;
            blocked_inputs = 0; stalled_outputs = 0;
            while (received < length) begin
                @(negedge clk);
                if (!pending && sent < length && (!pauses || local_cycle % 5 != 0)) pending = 1;
                in_valid = pending;
                in_last = pending && sent == length-1;
                if (sent < length) begin in_i = xi[sent]; in_q = xq[sent]; end
                out_ready = prolonged_stalls ? (local_cycle % 257 >= 160) :
                            (!pauses || local_cycle % 13 >= 5);
                @(posedge clk);
                if (sent == length && received < length && in_ready)
                    $fatal(1, "Entrada habilitada antes de aceptar out_last");
                if (in_valid && !in_ready) blocked_inputs = blocked_inputs + 1;
                if (out_valid && !out_ready) stalled_outputs = stalled_outputs + 1;
                if (in_valid && in_ready) begin
                    accepted_at[sent] = local_cycle;
                    if (!pauses && !prolonged_stalls && sent > 0 && accepted_at[sent]-accepted_at[sent-1] != 1)
                        $fatal(1, "Burbuja de entrada en muestra %0d", sent);
                    if (sent == 0) first_input = local_cycle;
                    sent = sent + 1; pending = 0;
                end
                if (out_valid && first_output == 0) first_output = local_cycle;
                if (out_valid && out_ready) begin
                    if (received >= sent) $fatal(1, "Salida sin entrada");
                    if ($signed(out_i) !== yi[received] || $signed(out_q) !== yq[received])
                        $fatal(1, "Trama %0d (%s) muestra %0d Q2.7: esperado (%0d,%0d), obtenido (%0d,%0d)",
                               frames, frame_name, received, yi[received], yq[received], out_i, out_q);
                    if (out_last !== (received == length-1)) $fatal(1, "out_last incorrecto");
                    if (!pauses && !prolonged_stalls && length % 8 == 0) begin
                        if (local_cycle-accepted_at[received] != EXPECTED_LATENCY)
                            $fatal(1, "Latencia muestra %0d: %0d, esperado %0d", received,
                                   local_cycle-accepted_at[received], EXPECTED_LATENCY);
                        if (received > 0 && local_cycle-previous_output != 1)
                            $fatal(1, "Burbuja de salida en muestra %0d", received);
                        if (received % 8 == 0) begin
                            if (received > 0 && local_cycle-previous_block != 8)
                                $fatal(1, "II de bloque distinto de ocho");
                            previous_block = local_cycle;
                        end
                    end
                    previous_output = local_cycle;
                    received = received + 1;
                end
                local_cycle = local_cycle + 1;
                if (local_cycle > 1000 + length*20) $fatal(1, "Timeout trama %s", frame_name);
                #1;
            end
            if (sent != length) $fatal(1, "Conteo de entradas incorrecto");
            if (prolonged_stalls && (blocked_inputs == 0 || stalled_outputs < 100))
                $fatal(1, "El escenario no lleno buffers ni retuvo salidas suficientemente");
            if (prolonged_stalls) long_stall_frames = long_stall_frames + 1;
            if (!pauses && !prolonged_stalls && length >= 2048) continuous_frames = continuous_frames + 1;
            @(negedge clk); in_valid = 0; in_last = 0; out_ready = 1;
            frames = frames + 1;
            $display("FRAME %s n=%0d pauses=%0d cycles=%0d first_valid_latency=%0d", frame_name, length, pauses,
                     local_cycle, first_output-first_input);
            repeat (2) begin @(posedge clk); if (out_valid) $fatal(1,"Salida extra entre tramas"); end
        end
    endtask

    // Abort by elapsed cycles, through the public interface: no dependency on
    // control implementation names. Eight samples launch a complete block.
    task automatic abort_frame(input integer samples, delay_cycles, input bit drain);
        integer sent;
        begin
            reset_filter();
            sent = 0;
            while (sent < samples) begin
                @(negedge clk); in_valid = 1; in_i = 1; in_q = -1; in_last = 0; out_ready = drain;
                @(posedge clk); if (in_ready) sent = sent + 1;
            end
            @(negedge clk); in_valid = 0;
            repeat (delay_cycles) @(negedge clk);
            reset_filter();
            repeat (32) begin @(posedge clk); if (out_valid) $fatal(1,"Resultado de trama abortada"); end
            for (sent=0; sent<8; sent=sent+1) begin xi[sent]=0; xq[sent]=0; end
            frame_name = "post_reset_zero_history";
            run_frame(8, 0);
        end
    endtask


    task automatic run_model_frames;
        integer count, frame_index, length, sample_index;
        begin
            if ($fscanf(vectors_fd, "%d", count) != 1 || count < 1)
                $fatal(1, "Faltan tramas de referencia A04");
            use_model_expected = 1;
            for (frame_index=0; frame_index<count; frame_index=frame_index+1) begin
                if ($fscanf(vectors_fd, "%s %d", frame_name, length) != 2 || length < 0 || length > MAX_SAMPLES)
                    $fatal(1, "Cabecera de trama A04 invalida");
                for (sample_index=0; sample_index<length; sample_index=sample_index+1) begin
                    if ($fscanf(vectors_fd, "%d %d %d %d", xi[sample_index], xq[sample_index],
                                yi[sample_index], yq[sample_index]) != 4)
                        $fatal(1, "Vector incompleto en %s muestra %0d", frame_name, sample_index);
                    if (xi[sample_index] < -1 || xi[sample_index] > 1 || xq[sample_index] < -1 || xq[sample_index] > 1)
                        $fatal(1, "Entrada fuera del dominio A04");
                end
                run_frame(length, 0);
                run_frame(length, 1);
            end
            $fclose(vectors_fd);
            use_model_expected = 0;
        end
    endtask

    task automatic run_a05_file(input string path, input bit pauses);
        integer fd, code, chars, next_index, length, frame_index;
        longint signed index, last, x_i, x_q, yt_i, yt_q, yf_i, yf_q;
        reg [4095:0] line, extra;
        begin
            fd = $fopen(path, "r");
            if (!fd) $fatal(1, "A05 %s indice 0: no se pudo abrir", path);
            next_index = 0; length = 0; frame_index = 0;
            use_model_expected = 1;
            while (!$feof(fd)) begin
                chars = $fgets(line, fd);
                if (chars > 0) begin
                    code = $sscanf(line, "%d %d %d %d %d %d %d %d %s",
                                   index, last, x_i, x_q, yt_i, yt_q, yf_i, yf_q, extra);
                    if (code != 8)
                        $fatal(1, "A05 %s indice %0d: se requieren ocho columnas", path, next_index);
                    // Icarus conserva X/Z al leer %d en longint; rechazar antes de comparar rangos.
                    if ((^{index, last, x_i, x_q, yt_i, yt_q, yf_i, yf_q}) === 1'bx)
                        $fatal(1, "A05 %s indice %0d: valor desconocido", path, next_index);
                    if (index != next_index)
                        $fatal(1, "A05 %s indice %0d: indice discontinuo %0d", path, next_index, index);
                    if (last < 0 || last > 1 || x_i < -1 || x_i > 1 || x_q < -1 || x_q > 1 ||
                        yt_i < -256 || yt_i > 255 || yt_q < -256 || yt_q > 255 ||
                        yf_i < -256 || yf_i > 255 || yf_q < -256 || yf_q > 255)
                        $fatal(1, "A05 %s indice %0d: valor fuera de rango", path, next_index);
                    if (length >= 2048)
                        $fatal(1, "A05 %s indice %0d: trama supera %0d muestras", path, next_index, 2048);
                    xi[length] = x_i; xq[length] = x_q;
                    yi[length] = yf_i; yq[length] = yf_q;
                    length = length + 1;
                    next_index = next_index + 1;
                    if (last == 1) begin
                        frame_name = $sformatf("%s trama=%0d base=%0d", path, frame_index, next_index-length);
                        run_frame(length, pauses);
                        frame_index = frame_index + 1;
                        length = 0;
                    end
                end else if (!$feof(fd))
                    $fatal(1, "A05 %s indice %0d: error de lectura", path, next_index);
            end
            $fclose(fd);
            if (next_index == 0) $fatal(1, "A05 %s indice 0: archivo vacio", path);
            if (length != 0)
                $fatal(1, "A05 %s indice %0d: trama sin last", path, next_index-1);
            use_model_expected = 0;
            $display("PASS A05 frequency_optimized %s: %0d muestras, %0d tramas, pausas=%0d",
                     path, next_index, frame_index, pauses);
        end
    endtask

    integer n, stage;
    string a05_file;
    initial begin
        if ($value$plusargs("a05_file=%s", a05_file)) begin
            reset_filter();
            run_a05_file(a05_file, 0);
            run_a05_file(a05_file, 1);
            $finish;
        end
        load_model_constants();
        reset_filter();
        repeat (12) begin @(posedge clk); if(out_valid) $fatal(1,"Salida en trama vacia"); end
        run_model_frames();
        for (stage=0; stage<2; stage=stage+1) begin
            run_a05_file("vectors/impulso.txt", stage != 0);
            run_a05_file("vectors/ceros.txt", stage != 0);
            run_a05_file("vectors/extremos_tiempo.txt", stage != 0);
            run_a05_file("vectors/extremos_frecuencia.txt", stage != 0);
            run_a05_file("vectors/bordes.txt", stage != 0);
            run_a05_file("build/vectors/qpsk_s1.txt", stage != 0);
        end
        for(n=0;n<4096;n=n+1) begin xi[n]=(n%3)-1; xq[n]=1-(n%3); end
        frame_name = "continuous_512_blocks";
        run_frame(4096, 0);
        prolonged_stalls = 1;
        frame_name = "buffers_full_long_stalls";
        run_frame(512, 1);
        prolonged_stalls = 0;
        abort_frame(3, 0, 0);
        // Sweep launch, FFT, spectral, IFFT, output conversion, held output and emission.
        for (stage=0; stage<=30; stage=stage+1) abort_frame(8, stage, stage % 2);
        // Multiple blocks in flight with both output buffers occupied.
        abort_frame(64, 160, 0);
        if (continuous_frames == 0 || long_stall_frames == 0) $fatal(1, "Falta cobertura de rendimiento/pausas");
        repeat (32) begin @(posedge clk); if(out_valid) $fatal(1,"Salida extra"); end
        $display("PASS frequency_optimized: %0d tramas; L=%0d, II_muestra=1, II_bloque=8; A04/A05, pausas y reset", frames, EXPECTED_LATENCY);
        $finish;
    end
endmodule
