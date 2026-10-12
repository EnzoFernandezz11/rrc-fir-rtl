`timescale 1ns/1ps

module tb_fir_frequency_serial;
    logic clk = 0;
    always #5 clk = ~clk;
    logic rst = 1;
    logic signed [1:0] in_i = 0, in_q = 0;
    logic in_valid = 0, in_last = 0, in_ready;
    logic signed [23:0] out_i, out_q;
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

    integer xi [0:127], xq [0:127];
    longint signed yi [0:127], yq [0:127];
    longint signed wr [0:15], wi [0:15];
    longint signed hr [0:15], hi [0:15];
    longint signed twr [0:7], twi [0:7], taps [0:7];
    real tap_float [0:7];
    integer cycles = 0, frames = 0;
    logic stalled = 0;
    logic signed [23:0] held_i, held_q;
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
                if (previous_done || products != 80 || $time/10-engine_start_cycle != 630)
                    $fatal(1, "Motor: pulso done, 80 productos o 630 ciclos incorrectos");
            end
            previous_done = dut.engine_done;
            if (out_valid && out_ready) begin
                block_outputs = block_outputs + 1;
                if (block_outputs == block_inputs) begin
                    if ($time/10-block_start+1 != 647+block_inputs+block_waits)
                        $fatal(1,"Presupuesto de bloque incorrecto");
                    measured_blocks = measured_blocks + 1;
                end
            end
        end
    end

    always @(posedge clk) begin
        cycles = cycles + 1;
        if (cycles > 150000) $fatal(1, "Timeout global");
        if (!rst && stalled &&
            (!out_valid || out_i !== held_i || out_q !== held_q || out_last !== held_last))
            $fatal(1, "Salida cambio durante backpressure");
        stalled = !rst && out_valid && !out_ready;
        held_i = out_i;
        held_q = out_q;
        held_last = out_last;
    end

    function automatic longint signed nearest_even(input real value);
        real base, fraction;
        longint signed n;
        begin
            base = $floor(value);
            n = $rtoi(base);
            fraction = value - base;
            if (fraction > 0.5 || (fraction == 0.5 && (n & 1))) n = n + 1;
            nearest_even = n;
        end
    endfunction

    function automatic integer reverse4(input integer n);
        reverse4 = ((n & 1) << 3) | ((n & 2) << 1) | ((n & 4) >> 1) | ((n & 8) >> 3);
    endfunction

    // Lee el bloque multilinea "coefficients" del archivo de configuracion del proyecto.
    task automatic load_taps;
        integer fd, status, index;
        reg [4095:0] line;
        reg [7:0] marker;
        bit found;
        begin
            fd = $fopen("config/project.json", "r");
            if (!fd) $fatal(1, "No se pudo abrir config/project.json; ejecutar desde raiz del repo");
            found = 0;
            while (!$feof(fd) && !found) begin
                status = $fgets(line, fd);
                if ($sscanf(line, " \"coefficients\": %c", marker) == 1 && marker == "[") begin
                    for (index = 0; index < 8; index = index + 1) begin
                        status = $fscanf(fd, " %f,", tap_float[index]);
                        if (status != 1) $fatal(1,"Se requieren ocho coeficientes numericos en config/project.json");
                    end
                    found = 1;
                end
            end
            $fclose(fd);
            if (!found) $fatal(1,"No se encontro coefficients en config/project.json");
        end
    endtask

    function automatic longint signed checked_work(input longint signed value);
        begin
            if (value < -64'sd2147483648 || value > 64'sd2147483647)
                $fatal(1, "Overflow provisional en referencia: %0d", value);
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
                        tr = checked_work((wr[b]*cr - wi[b]*ci) >>> 16);
                        ti = checked_work((wr[b]*ci + wi[b]*cr) >>> 16);
                        wr[a] = checked_work(ar + tr); wi[a] = checked_work(ai + ti);
                        wr[b] = checked_work(ar - tr); wi[b] = checked_work(ai - ti);
                    end
        end
    endtask

    task automatic reference_frame(input integer length);
        integer offset, r, n, k, rev;
        longint signed tr, ti;
        real expected_i, expected_q, error_i, error_q;
        begin
            for (offset = 0; offset < length; offset = offset + 8) begin
                for (r = 0; r < 16; r = r + 1) begin
                    n = offset - 8 + r;
                    rev = reverse4(r);
                    wr[rev] = (n >= 0 && n < length) ? 64'(xi[n]) * 65536 : 0;
                    wi[rev] = (n >= 0 && n < length) ? 64'(xq[n]) * 65536 : 0;
                end
                transform(0);
                for (k = 0; k < 16; k = k + 1) begin
                    tr = checked_work((wr[k]*hr[k] - wi[k]*hi[k]) >>> 16);
                    ti = checked_work((wr[k]*hi[k] + wi[k]*hr[k]) >>> 16);
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
                    yi[offset+r] = wr[8+r] >>> 4;
                    yq[offset+r] = wi[8+r] >>> 4;
                end
            end
            // Convolucion causal independiente: detecta errores de signo, orden y ganancia.
            for (n = 0; n < length; n = n + 1) begin
                expected_i = 0; expected_q = 0;
                for (k = 0; k < 8 && k <= n; k = k + 1) begin
                    expected_i = expected_i + tap_float[k] * xi[n-k];
                    expected_q = expected_q + tap_float[k] * xq[n-k];
                end
                error_i = yi[n] / 65536.0 - expected_i;
                error_q = yq[n] / 65536.0 - expected_q;
                if (error_i > 0.001 || error_i < -0.001 || error_q > 0.001 || error_q < -0.001)
                    $fatal(1, "Referencia difiere de convolucion en %0d", n);
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
        integer accepted_at [0:127];
        bit pending;
        begin
            reference_frame(length);
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
                    if (!pauses && sent > 0 && accepted_at[sent]-accepted_at[sent-1] != ((sent%8 == 0) ? 648 : 1))
                        $fatal(1,"Intervalo entre aceptaciones incorrecto");
                    if (sent == 0) first_input = $time / 10;
                    sent = sent + 1; pending = 0;
                end
                if (out_valid && first_output == 0) first_output = $time / 10;
                if (out_valid && out_ready) begin
                    if (!pauses && $time/10-accepted_at[received] != 639)
                        $fatal(1,"Latencia por muestra incorrecta");
                    if ($signed(out_i) !== yi[received] || $signed(out_q) !== yq[received])
                        $fatal(1, "Trama %0d muestra %0d: esperado (%0d,%0d), obtenido (%0d,%0d)",
                               frames, received, yi[received], yq[received], out_i, out_q);
                    if (out_last !== (received == length-1)) $fatal(1, "out_last incorrecto");
                    received = received + 1;
                end
                local_cycle = local_cycle + 1;
                if (local_cycle > 20000) $fatal(1, "Timeout trama");
                #1;
            end
            if (sent != length) $fatal(1, "Conteo de entradas incorrecto");
            if (!pauses && first_output-first_input != 639) $fatal(1,"Latencia ideal distinta de 639");
            @(negedge clk); in_valid = 0; in_last = 0; out_ready = 1;
            frames = frames + 1;
            $display("FRAME n=%0d pauses=%0d cycles=%0d first_valid_latency=%0d", length, pauses,
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
            if (mul_done) $fatal(1, "done prematuro");
            @(negedge clk); mul_start = 0;
            repeat (4) begin @(posedge clk); #1; if (mul_done) $fatal(1, "done prematuro"); end
            @(posedge clk); #1;
            if (!mul_done || p_i != expected_r || p_q != expected_i) $fatal(1, "Producto complejo incorrecto");
            @(posedge clk); #1;
            if (mul_done || p_i != expected_r || p_q != expected_i) $fatal(1, "Pulso/retencion incorrecto");
        end
    endtask

    task automatic send_one(input bit last_sample);
        begin
            @(negedge clk); in_valid = 1; in_i = 1; in_q = -1; in_last = last_sample;
            do @(posedge clk); while (!in_ready);
            @(negedge clk); in_valid = 0; in_last = 0;
        end
    endtask

    integer n, k, length, pos, stage;
    logic [31:0] random_state = 32'hc02f1234;
    real angle, sum_r, sum_i;
    initial begin
        // TODO(A04): perfil provisional, no contrato numerico definitivo.
        load_taps();
        for (n=0; n<8; n=n+1) begin
            taps[n] = nearest_even(tap_float[n]*65536.0);
            angle = -2.0*3.141592653589793*n/16.0;
            twr[n] = nearest_even($cos(angle)*65536.0);
            twi[n] = nearest_even($sin(angle)*65536.0);
        end
        for (k=0; k<16; k=k+1) begin
            sum_r=0; sum_i=0;
            for (n=0; n<8; n=n+1) begin
                angle = -2.0*3.141592653589793*k*n/16.0;
                sum_r = sum_r + taps[n]*$cos(angle);
                sum_i = sum_i + taps[n]*$sin(angle);
            end
            hr[k]=nearest_even(sum_r); hi[k]=nearest_even(sum_i);
        end
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
        for (stage=0; stage<6; stage=stage+1) begin
            @(negedge clk); mul_start=1;
            @(posedge clk); #1;
            @(negedge clk); mul_start=0;
            repeat (stage) @(negedge clk);
            mul_rst=1;
            @(posedge clk); #1;
            if (mul_done || p_i || p_q) $fatal(1, "Reset del multiplicador");
            @(negedge clk); mul_rst=0;
            repeat (7) begin @(posedge clk); #1; if(mul_done) $fatal(1,"done luego de abortar"); end
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
        for(n=0;n<64;n=n+1) begin xi[n]=(n%3)-1; xq[n]=(n%4)-2; end
        run_frame(64,1);
        for(n=0;n<32;n=n+1) begin xi[n]=-2; xq[n]=-2; end
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
        repeat(12) begin @(posedge clk); if(out_valid) $fatal(1,"Salida extra"); end
        $display("PASS frequency_serial: %0d tramas, %0d bloques; L=639, bloque=655, intervalo=648; perfil provisional",frames,measured_blocks);
        $finish;
    end
endmodule
