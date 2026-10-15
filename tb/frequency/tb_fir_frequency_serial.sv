`timescale 1ns/1ps

module tb_fir_frequency_serial;
    localparam integer MAX_SAMPLES = 2048;
    logic clk = 0;
    always #5 clk = ~clk;
    logic rst = 1;
    logic signed [1:0] in_i = 0, in_q = 0;
    logic in_valid = 0, in_last = 0, in_ready;
    logic signed [8:0] out_i, out_q;
    logic out_valid, out_last, out_ready = 0;

    fir_frequency_serial dut (.*);

    logic mul_rst = 1, mul_start = 0, mul_done;
    logic signed [3:0] a_i = 0, a_q = 0, b_i = 0, b_q = 0;
    logic signed [8:0] p_i, p_q;
    complex_mul_serial #(.W_A(4), .W_B(4), .W_P(9)) mul (
        .clk(clk), .rst(mul_rst), .start(mul_start),
        .a_i(a_i), .a_q(a_q), .b_i(b_i), .b_q(b_q),
        .p_i(p_i), .p_q(p_q), .done(mul_done)
    );

    logic wide_mul_done;
    logic signed [11:0] wide_p_i, wide_p_q;
    complex_mul_serial #(.W_A(4), .W_B(4), .W_P(12)) wide_mul (
        .clk(clk), .rst(mul_rst), .start(mul_start),
        .a_i(a_i), .a_q(a_q), .b_i(b_i), .b_q(b_q),
        .p_i(wide_p_i), .p_q(wide_p_q), .done(wide_mul_done)
    );

    integer xi [0:MAX_SAMPLES-1], xq [0:MAX_SAMPLES-1];
    longint signed yi [0:MAX_SAMPLES-1], yq [0:MAX_SAMPLES-1];
    longint signed wr [0:15], wi [0:15];
    longint signed hr [0:15], hi [0:15];
    longint signed twr [0:7], twi [0:7], taps [0:7];
    integer vectors_fd;
    integer rounding_value;
    string frame_name = "local";
    bit use_model_expected = 0;
    integer cycles = 0, frames = 0;
    logic stalled = 0;
    logic signed [8:0] held_i, held_q;
    logic held_last;
    integer block_start = 0, block_waits = 0, block_inputs = 0, block_outputs = 0;
    integer engine_start_cycle = 0, products = 0, measured_blocks = 0;
    bit previous_done = 0;

    // Presupuesto completo: copia, captura/relleno, motor, enlace y emision.
    always @(posedge clk) begin
        if (rst) begin
            block_start = 0;
            previous_done = 0;
        end else begin
            if (dut.engine_load_en && dut.engine_load_index == 0) begin
                block_start = $time / 10;
                block_waits = 0; block_inputs = 0; block_outputs = 0;
            end
            if (in_valid && in_ready) block_inputs = block_inputs + 1;
            if (in_ready && !in_valid) block_waits = block_waits + 1;
            if (out_valid && !out_ready) block_waits = block_waits + 1;
            if (dut.engine_start) begin
                engine_start_cycle = $time / 10;
                products = 0;
            end
            if (dut.u_engine.mul_start) products = products + 1;
            if (dut.engine_done) begin
                if (previous_done || products != 80 || $time/10-engine_start_cycle != 550)
                    $fatal(1, "Motor: pulso done, 80 productos o 550 ciclos incorrectos");
            end
            previous_done = dut.engine_done;
            if (out_valid && out_ready) begin
                block_outputs = block_outputs + 1;
                if (block_outputs == block_inputs) begin
                    if ($time/10-block_start+1 != 567+block_inputs+block_waits)
                        $fatal(1,"Presupuesto de bloque incorrecto");
                    measured_blocks = measured_blocks + 1;
                end
            end
        end
    end

    always @(posedge clk) begin
        cycles = cycles + 1;
        if (cycles > 2000000) $fatal(1, "Timeout global");
        if (!rst && stalled &&
            (!out_valid || out_i !== held_i || out_q !== held_q || out_last !== held_last))
            $fatal(1, "Salida cambio durante backpressure");
        stalled = !rst && out_valid && !out_ready;
        held_i = out_i;
        held_q = out_q;
        held_last = out_last;
    end

    function automatic longint signed round_shift(input longint signed value, input integer shift);
        round_shift = (shift == 0) ? value : (value + (64'sd1 << (shift-1))) >>> shift;
    endfunction

    function automatic integer reverse4(input integer n);
        reverse4 = ((n & 1) << 3) | ((n & 2) << 1) | ((n & 4) >> 1) | ((n & 8) >> 3);
    endfunction

    // Constantes y vectores salen del mismo modelo A04 usado por Python.
    task automatic load_model_constants;
        integer w_work, f_work, w_coef, f_coef, w_out, f_out, index;
        begin
            vectors_fd = $fopen("build/frequency_serial_vectors.txt", "r");
            if (!vectors_fd) $fatal(1, "Faltan vectores A04: ejecutar make smoke desde la raiz");
            if ($fscanf(vectors_fd, "%d %d %d %d %d %d", w_work, f_work, w_coef, f_coef, w_out, f_out) != 6)
                $fatal(1, "Cabecera de formatos A04 invalida");
            if (w_work != dut.W_WORK || f_work != dut.F_WORK || w_coef != dut.W_COEF ||
                f_coef != dut.F_COEF || w_out != dut.W_OUT || f_out != dut.F_OUT)
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

    // La referencia genera direcciones por etapas, sin copiar el case del RTL.
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
            @(posedge clk); #1;
            @(negedge clk); rst = 0;
            repeat (8) begin
                @(posedge clk);
                if (in_ready || out_valid) $fatal(1, "Aceptacion durante copia inicial");
                #1;
            end
            if (!in_ready) $fatal(1, "Faltan ocho ciclos de copia inicial");
        end
    endtask

    task automatic run_frame(input integer length, input bit pauses);
        integer sent, received, local_cycle, started, first_input, first_output;
        integer accepted_at [0:MAX_SAMPLES-1];
        bit pending;
        begin
            if (!use_model_expected) reference_frame(length);
            sent = 0; received = 0; local_cycle = 0; pending = 0;
            started = cycles; first_input = 0; first_output = 0;
            while (received < length) begin
                @(negedge clk);
                if (!pending && sent < length && (!pauses || local_cycle % 5 != 0)) pending = 1;
                in_valid = pending;
                in_last = pending && sent == length-1;
                if (sent < length) begin in_i = xi[sent]; in_q = xq[sent]; end
                out_ready = !pauses || (local_cycle % 13 >= 5);
                @(posedge clk);
                if (in_valid && in_ready) begin
                    accepted_at[sent] = $time / 10;
                    if (!pauses && sent > 0 && accepted_at[sent]-accepted_at[sent-1] != ((sent%8 == 0) ? 568 : 1))
                        $fatal(1,"Intervalo entre aceptaciones incorrecto");
                    if (sent == 0) first_input = $time / 10;
                    sent = sent + 1; pending = 0;
                end
                if (out_valid && first_output == 0) first_output = $time / 10;
                if (out_valid && out_ready) begin
                    if (!pauses && $time/10-accepted_at[received] != 559)
                        $fatal(1,"Latencia por muestra incorrecta");
                    if ($signed(out_i) !== yi[received] || $signed(out_q) !== yq[received])
                        $fatal(1, "Trama %0d (%s) muestra %0d Q2.7: esperado (%0d,%0d), obtenido (%0d,%0d)",
                               frames, frame_name, received, yi[received], yq[received], out_i, out_q);
                    if (out_last !== (received == length-1)) $fatal(1, "out_last incorrecto");
                    received = received + 1;
                end
                local_cycle = local_cycle + 1;
                if (local_cycle > 1000 + ((length+7)/8)*800) $fatal(1, "Timeout trama");
                #1;
            end
            if (sent != length) $fatal(1, "Conteo de entradas incorrecto");
            if (!pauses && first_output-first_input != 559) $fatal(1,"Latencia ideal distinta de 559");
            @(negedge clk); in_valid = 0; in_last = 0; out_ready = 1;
            frames = frames + 1;
            $display("FRAME %s n=%0d pauses=%0d cycles=%0d first_valid_latency=%0d", frame_name, length, pauses,
                     cycles-started, first_output-first_input);
            repeat (2) begin @(posedge clk); if (out_valid) $fatal(1,"Salida extra entre tramas"); end
        end
    endtask

    task automatic check_mul(input integer ar, ai, br, bi);
        integer expected_r, expected_i;
        begin
            expected_r = ar*br-ai*bi; expected_i = ar*bi+ai*br;
            @(negedge clk); a_i = ar; a_q = ai; b_i = br; b_q = bi; mul_start = 1;
            @(posedge clk); #1;
            if (mul_done || wide_mul_done) $fatal(1, "done prematuro");
            // Los operandos quedan capturados; las entradas pueden cambiar.
            @(negedge clk); mul_start = 0; a_i = 0; a_q = 0; b_i = 0; b_q = 0;
            repeat (3) begin
                @(posedge clk); #1;
                if (mul_done || wide_mul_done) $fatal(1, "done prematuro");
            end
            @(posedge clk); #1;
            if (!mul_done || !wide_mul_done || p_i != expected_r || p_q != expected_i ||
                wide_p_i != expected_r || wide_p_q != expected_i)
                $fatal(1, "Producto complejo incorrecto (%0d,%0d)*(%0d,%0d)", ar, ai, br, bi);
            @(posedge clk); #1;
            if (mul_done || wide_mul_done || p_i != expected_r || p_q != expected_i ||
                wide_p_i != expected_r || wide_p_q != expected_i)
                $fatal(1, "Pulso/retencion incorrecto");
        end
    endtask

    task automatic check_product_rounding(input integer value, expected);
        begin
            rounding_value = value;
            force dut.u_engine.u_complex_mul_serial.p_i = rounding_value;
            force dut.u_engine.u_complex_mul_serial.p_q = rounding_value;
            #1;
            if (dut.u_engine.rounded_product_i !== expected || dut.u_engine.rounded_product_q !== expected)
                $fatal(1, "Redondeo de producto: %0d esperado %0d", value, expected);
            release dut.u_engine.u_complex_mul_serial.p_i;
            release dut.u_engine.u_complex_mul_serial.p_q;
        end
    endtask

    task automatic send_one(input bit last_sample);
        begin
            @(negedge clk); in_valid = 1; in_i = 1; in_q = -1; in_last = last_sample;
            do @(posedge clk); while (!in_ready);
            @(negedge clk); in_valid = 0; in_last = 0;
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
                run_frame(length, (length == 0) || (frame_index % 2 == 0));
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
                    if ((^{index, last, x_i, x_q, yt_i, yt_q, yf_i, yf_q}) === 1'bx)
                        $fatal(1, "A05 %s indice %0d: valor desconocido", path, next_index);
                    if (index != next_index)
                        $fatal(1, "A05 %s indice %0d: indice discontinuo %0d", path, next_index, index);
                    if (last < 0 || last > 1 || x_i < -1 || x_i > 1 || x_q < -1 || x_q > 1 ||
                        yt_i < -256 || yt_i > 255 || yt_q < -256 || yt_q > 255 ||
                        yf_i < -256 || yf_i > 255 || yf_q < -256 || yf_q > 255)
                        $fatal(1, "A05 %s indice %0d: valor fuera de rango", path, next_index);
                    if (length >= MAX_SAMPLES)
                        $fatal(1, "A05 %s indice %0d: trama supera %0d muestras", path, next_index, MAX_SAMPLES);
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
            $display("PASS A05 frequency_serial %s: %0d muestras, %0d tramas, pausas=%0d",
                     path, next_index, frame_index, pauses);
        end
    endtask

    integer n, k, length, pos, stage;
    integer ar_index, ai_index, br_index, bi_index;
    integer mul_values [0:3];
    logic [31:0] random_state = 32'hc02f1234;
    string a05_file;
    initial begin
        if ($value$plusargs("a05_file=%s", a05_file)) begin
            reset_filter();
            run_a05_file(a05_file, 0);
            run_a05_file(a05_file, 1);
            $finish;
        end
        load_model_constants();
        check_product_rounding(127, 0);
        check_product_rounding(128, 1);
        check_product_rounding(-128, 0);
        check_product_rounding(-129, -1);
        check_product_rounding(384, 2);
        check_product_rounding(-384, -1);
        check_product_rounding(4194303, 16384);
        check_product_rounding(-4194304, -16384);
        if ($test$plusargs("dump_constants")) begin
            for (n=0;n<8;n=n+1) $display("h_q[%0d]=%0d W[%0d]=(%0d,%0d)",n,taps[n],n,twr[n],twi[n]);
            for (k=0;k<16;k=k+1) $display("H[%0d]=(%0d,%0d)",k,hr[k],hi[k]);
        end
        repeat (2) @(posedge clk);
        @(negedge clk); mul_rst=0;
        check_mul(0,0,7,-8);
        check_mul(-8,-8,-8,-8);
        check_mul(7,-8,-8,7);
        check_mul(7,7,7,7);
        check_mul(-3,5,6,-2);
        mul_values[0]=-8; mul_values[1]=-1; mul_values[2]=0; mul_values[3]=7;
        for (ar_index=0; ar_index<4; ar_index=ar_index+1)
            for (ai_index=0; ai_index<4; ai_index=ai_index+1)
                for (br_index=0; br_index<4; br_index=br_index+1)
                    for (bi_index=0; bi_index<4; bi_index=bi_index+1)
                        check_mul(mul_values[ar_index], mul_values[ai_index],
                                  mul_values[br_index], mul_values[bi_index]);
        for (stage=0; stage<6; stage=stage+1) begin
            @(negedge clk); mul_start=1; a_i=-8; a_q=7; b_i=-1; b_q=-8;
            @(posedge clk); #1;
            @(negedge clk); mul_start=0;
            repeat (stage) @(negedge clk);
            mul_rst=1;
            @(posedge clk); #1;
            if (mul_done || wide_mul_done || p_i || p_q || wide_p_i || wide_p_q)
                $fatal(1, "Reset del multiplicador");
            @(negedge clk); mul_rst=0;
            repeat (7) begin
                @(posedge clk); #1;
                if (mul_done || wide_mul_done || p_i || p_q || wide_p_i || wide_p_q)
                    $fatal(1,"Resultado luego de abortar");
            end
            check_mul(-3,5,6,-2);
        end
        reset_filter();
        repeat (12) begin @(posedge clk); if(out_valid) $fatal(1,"Salida en trama vacia"); end
        for (length=1; length<=17; length=length+1) begin
            for(n=0;n<length;n=n+1) begin
                xi[n] = (n%2) ? 0 : ((n%4) ? -1 : 1);
                xq[n] = (n%2) ? 0 : ((n%6) ? 1 : -1);
            end
            run_frame(length, 1);
        end
        for (pos=0; pos<18; pos=pos+1) begin
            for(n=0;n<25;n=n+1) begin xi[n]=0; xq[n]=0; end
            xi[pos]=1; xq[pos]=-1;
            run_frame(25, 0);
        end
        for(n=0;n<64;n=n+1) begin xi[n]=(n%3)-1; xq[n]=1-(n%3); end
        run_frame(64,1);
        for(n=0;n<32;n=n+1) begin xi[n]=-1; xq[n]=-1; end
        run_frame(32,0);
        for(n=0;n<32;n=n+1) begin xi[n]=1; xq[n]=1; end
        run_frame(32,0);
        for(n=0;n<32;n=n+1) begin xi[n]=0; xq[n]=0; end
        run_frame(32,0);
        for(n=0;n<128;n=n+2) begin
            random_state = {random_state[30:0], random_state[31]^random_state[21]^random_state[1]^random_state[0]};
            xi[n] = random_state[0] ? 1 : -1; xq[n] = random_state[1] ? 1 : -1;
            xi[n+1] = 0; xq[n+1] = 0;
        end
        run_frame(128,1);
        // Reset en captura, relleno, calculo, salida detenida y copia.
        reset_filter(); send_one(0); reset_filter();
        send_one(1); reset_filter();
        send_one(1); wait(dut.u_engine.start); repeat(20) @(negedge clk); reset_filter();
        send_one(1); wait(out_valid); repeat(4) @(negedge clk); reset_filter();
        @(negedge clk); rst=1;
        @(negedge clk); rst=0;
        repeat(3) @(negedge clk); reset_filter();
        for(n=0;n<8;n=n+1) begin xi[n]=1; xq[n]=-1; end
        run_frame(8,0);
        for(stage=0;stage<4;stage=stage+1) begin
            send_one(1);
            case(stage)
                0: wait(dut.u_engine.u_control.phase == dut.u_engine.u_control.PH_MUL);
                1: wait(dut.u_engine.u_control.state == dut.u_engine.u_control.ST_REORDER);
                2: begin
                    wait(dut.u_engine.u_control.phase == dut.u_engine.u_control.PH_IFFT);
                    repeat(15) @(negedge clk);
                end
                3: wait(dut.engine_done);
            endcase
            reset_filter();
            run_frame(8,0);
        end
        run_model_frames();
        for (stage=0; stage<2; stage=stage+1) begin
            run_a05_file("vectors/impulso.txt", stage != 0);
            run_a05_file("vectors/ceros.txt", stage != 0);
            run_a05_file("vectors/extremos_tiempo.txt", stage != 0);
            run_a05_file("vectors/extremos_frecuencia.txt", stage != 0);
            run_a05_file("vectors/bordes.txt", stage != 0);
            run_a05_file("build/vectors/qpsk_s1.txt", stage != 0);
        end
        repeat(12) begin @(posedge clk); if(out_valid) $fatal(1,"Salida extra"); end
        $display("PASS frequency_serial: %0d tramas, %0d bloques; L=559, bloque=575, intervalo=568; formatos A04 y vector matching Python/A05",frames,measured_blocks);
        $finish;
    end
endmodule
