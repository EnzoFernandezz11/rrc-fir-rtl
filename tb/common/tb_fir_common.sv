// A06: banco común de verificación. Corre cualquier variante registrada con los
// mismos vectores de A05 y las mismas pruebas de protocolo (interfaz-rtl.md).
//   iverilog -g2012 -DFIR_DUT=<rtl_top> -s tb_fir_common <fuentes> tb/common/tb_fir_common.sv
//   vvp <salida> +variante=<name> +dominio=time|frequency [+regresion]
// scripts/ci.py lo hace para cada variante de config/rtl_targets.json.
//
// Por cada archivo de vectores:
//   1. reset en medio de una trama con un resultado pendiente (regla 6): la
//      corrida siguiente no debe verlo ni usar historial viejo;
//   2. ideal (entrada siempre disponible, out_ready = 1): compara y mide L e II;
//   3. con pausas: burbujas y out_ready = 0 pseudoaleatorios (reglas 2 y 7).
// Compara por índice de resultado aceptado contra yt (time) o yf (frequency).
`ifndef FIR_DUT
`define FIR_DUT fir_time_serial
`endif

module tb_fir_common;

    localparam int W_IN    = 2;
    localparam int W_OUT   = 9;   // Q2.7 (A04)
    localparam int MAX_N   = 4096;
    localparam int SEMILLA = 1;

    logic clk = 0;
    logic rst = 1;
    logic signed [W_IN-1:0] in_i = 0;
    logic signed [W_IN-1:0] in_q = 0;
    logic in_valid  = 0;
    logic in_last   = 0;
    logic out_ready = 0;
    wire  in_ready, out_valid, out_last;
    wire  signed [W_OUT-1:0] out_i, out_q;

    `FIR_DUT dut (
        .clk(clk), .rst(rst),
        .in_i(in_i), .in_q(in_q), .in_valid(in_valid), .in_last(in_last), .in_ready(in_ready),
        .out_i(out_i), .out_q(out_q), .out_valid(out_valid), .out_last(out_last), .out_ready(out_ready)
    );

    always #5 clk = ~clk;

    string variante = "?";
    logic  frecuencia = 0;  // compara contra yf en vez de yt

    // Vectores del archivo en curso.
    integer v_last [0:MAX_N-1];
    integer v_x_i  [0:MAX_N-1];
    integer v_x_q  [0:MAX_N-1];
    integer v_y_i  [0:MAX_N-1];
    integer v_y_q  [0:MAX_N-1];
    integer n_tot;

    // Estado de la corrida.
    string  archivo, modo;
    logic   corriendo = 0;
    logic   con_pausas = 0;
    logic   retener = 0;  // out_ready = 0 para dejar un resultado pendiente
    integer semilla_in, semilla_out;
    integer n_in, n_out, presentada, ciclo;
    logic   visto;   // out_valid ya visto para el resultado n_out
    logic   sostenido;
    logic signed [W_OUT-1:0] s_i, s_q;
    logic   s_last;
    integer t_acepta [0:MAX_N-1];
    integer t_valido [0:MAX_N-1];

    task automatic falla(input string que);
        $fatal(1, "FALLA %s %s (%s, semilla %0d) índice %0d: %s",
               variante, archivo, modo, SEMILLA, n_out, que);
    endtask

    // Monitor: transferencias y reglas del lado de la salida, con los valores del ciclo.
    always @(posedge clk) begin
        if (rst) begin
            sostenido = 0;
        end else begin
            ciclo = ciclo + 1;
            // Regla 2: un resultado no aceptado se sostiene sin cambios.
            if (sostenido && !out_valid)
                falla("out_valid bajó sin transferencia (regla 2)");
            if (sostenido && (out_i !== s_i || out_q !== s_q || out_last !== s_last))
                falla($sformatf("la salida cambió con out_ready = 0: %0d/%0d last=%0d -> %0d/%0d last=%0d (regla 2)",
                                s_i, s_q, s_last, out_i, out_q, out_last));
            sostenido = out_valid && !out_ready;
            s_i = out_i;
            s_q = out_q;
            s_last = out_last;

            if (in_valid && in_ready) begin
                t_acepta[n_in] = ciclo;
                n_in = n_in + 1;
            end
            if (out_valid && !visto) begin
                t_valido[n_out] = ciclo;
                visto = 1;
            end
            if (out_valid && out_ready) begin
                // Las aceptaciones de este flanco ya se contaron: un resultado
                // sin su muestra es un resultado pendiente de antes del reset.
                if (n_out >= n_in)
                    falla($sformatf("resultado sin muestra aceptada (%0d aceptadas; reglas 4 y 6)", n_in));
                if (out_i !== v_y_i[n_out] || out_q !== v_y_q[n_out] || out_last !== (v_last[n_out] != 0))
                    falla($sformatf("esperado I/Q = %0d/%0d last=%0d, obtenido %0d/%0d last=%0d (enteros Q2.7, columna %s)",
                                    v_y_i[n_out], v_y_q[n_out], v_last[n_out] != 0, out_i, out_q, out_last,
                                    frecuencia ? "yf" : "yt"));
                n_out = n_out + 1;
                visto = 0;
            end
        end
    end

    // Productor y receptor: cambian sus señales en el flanco descendente.
    always @(negedge clk) begin
        if (!rst && corriendo) begin
            // Regla 2: la muestra presentada se retira solo después de su transferencia.
            if (in_valid && n_in > presentada) begin
                in_valid = 0;
                in_i     = 'x;  // regla 1: sin valid los datos no significan nada
                in_q     = 'x;
                in_last  = 'x;
            end
            if (!in_valid && n_in < n_tot && !(con_pausas && $random(semilla_in) % 4 == 0)) begin
                in_i       = v_x_i[n_in];
                in_q       = v_x_q[n_in];
                in_last    = v_last[n_in] != 0;
                presentada = n_in;
                in_valid   = 1;
            end
            out_ready = retener ? 0 : con_pausas ? ($random(semilla_out) % 3 != 0) : 1;
        end
    end

    task automatic cargar(input string ruta);
        integer fd, code, n, last, x_i, x_q, yt_i, yt_q, yf_i, yf_q;
        fd = $fopen(ruta, "r");
        if (fd == 0) $fatal(1, "no se pudo abrir %s", ruta);
        n_tot = 0;
        while (!$feof(fd)) begin
            code = $fscanf(fd, "%d %d %d %d %d %d %d %d\n", n, last, x_i, x_q, yt_i, yt_q, yf_i, yf_q);
            if (code == 8) begin
                if (n != n_tot) $fatal(1, "%s: índice %0d fuera de orden", ruta, n);
                if (n_tot >= MAX_N) $fatal(1, "%s: más de %0d muestras", ruta, MAX_N);
                v_last[n_tot] = last;
                v_x_i[n_tot]  = x_i;
                v_x_q[n_tot]  = x_q;
                v_y_i[n_tot]  = frecuencia ? yf_i : yt_i;
                v_y_q[n_tot]  = frecuencia ? yf_q : yt_q;
                n_tot = n_tot + 1;
            end
        end
        $fclose(fd);
        if (n_tot == 0) $fatal(1, "%s: no tiene muestras", ruta);
        archivo = ruta;
    endtask

    // Reset de un solo flanco, el mínimo de la regla 6; el monitor no cuenta nada mientras rst = 1.
    task automatic resetear();
        @(negedge clk);
        rst = 1;
        corriendo = 0;
        in_valid  = 0;
        out_ready = 0;
        n_in = 0;
        n_out = 0;
        ciclo = 0;
        visto = 0;
        presentada = -1;
        @(negedge clk);
        rst = 0;
    endtask

    // Regla 6: con pausas hasta aceptar unas muestras de la primera trama, después
    // retiene la salida y resetea con un resultado pendiente. El productor sigue
    // sosteniendo su muestra hasta el reset (regla 2).
    task automatic reset_en_trama();
        integer corte, espera;
        modo = "reset en trama";
        con_pausas  = 1;
        semilla_in  = SEMILLA + 2;
        semilla_out = SEMILLA + 3;
        corte = 1;
        while (corte < 5 && corte < n_tot && v_last[corte - 1] == 0) corte++;
        resetear();
        corriendo = 1;
        espera = 0;
        while (n_in < corte || !out_valid) begin
            @(negedge clk);
            retener = n_in >= corte;
            if (++espera > 2000 * corte + 5000) falla("timeout esperando un resultado pendiente");
        end
        retener = 0;
    endtask

    task automatic correr(input logic pausas);
        integer espera, l_max, ii_max;
        real    ciclos_muestra;
        modo        = pausas ? "con pausas" : "ideal";
        con_pausas  = pausas;
        semilla_in  = SEMILLA;
        semilla_out = SEMILLA + 1;
        resetear();
        corriendo = 1;

        espera = 0;
        while (n_out < n_tot) begin
            @(negedge clk);
            if (++espera > 2000 * n_tot + 5000)
                falla($sformatf("timeout con %0d de %0d resultados", n_out, n_tot));
        end

        // Más ciclos sin entrada: no debe aparecer ningún resultado extra.
        corriendo = 0;
        in_valid  = 0;
        out_ready = 1;
        repeat (100) @(negedge clk);
        if (out_valid) falla("resultado extra después del último");
        if (n_in != n_tot) falla($sformatf("%0d muestras aceptadas de %0d", n_in, n_tot));

        if (!pausas) begin
            // L e II con entrada siempre disponible y out_ready = 1 (interfaz-rtl.md).
            l_max = 0;
            ii_max = 0;
            for (int n = 0; n < n_tot; n++) begin
                if (t_valido[n] - t_acepta[n] > l_max) l_max = t_valido[n] - t_acepta[n];
                if (n > 0 && t_acepta[n] - t_acepta[n-1] > ii_max) ii_max = t_acepta[n] - t_acepta[n-1];
            end
            ciclos_muestra = n_tot > 1 ? real'(t_acepta[n_tot-1] - t_acepta[0]) / (n_tot - 1) : 0.0;
            $display("OK %s %s ideal: %0d muestras; L máx = %0d, II máx = %0d, %.2f ciclos/muestra",
                     variante, archivo, n_tot, l_max, ii_max, ciclos_muestra);
        end else begin
            $display("OK %s %s con pausas (semilla %0d): %0d muestras en %0d ciclos",
                     variante, archivo, SEMILLA, n_tot, ciclo);
        end
    endtask

    task automatic verificar(input string ruta);
        cargar(ruta);
        reset_en_trama();
        correr(0);
        correr(1);
    endtask

    initial begin
        string dominio;
        if (!$value$plusargs("variante=%s", variante)) $fatal(1, "falta +variante=<name>");
        if (!$value$plusargs("dominio=%s", dominio)) $fatal(1, "falta +dominio=time|frequency");
        if (dominio != "time" && dominio != "frequency") $fatal(1, "dominio inválido: %s", dominio);
        frecuencia = dominio == "frequency";

        verificar("vectors/impulso.txt");
        verificar("vectors/ceros.txt");
        verificar("vectors/extremos_tiempo.txt");
        verificar("vectors/extremos_frecuencia.txt");
        verificar("vectors/bordes.txt");
        if ($test$plusargs("regresion"))
            verificar("build/vectors/qpsk_s1.txt");
        $display("PASS %s: banco común (vector matching y protocolo)", variante);
        $finish;
    end

endmodule
