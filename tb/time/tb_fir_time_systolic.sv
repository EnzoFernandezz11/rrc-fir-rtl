// B04: testbench de fir_time_systolic, adaptado del de B02 (tb_fir_time_serial).
// Compara cada resultado aceptado con las columnas yt de vectors/ (modelo fijo
// fir_time_fxp, A05), por índice y no por ciclo (docs/contratos/verificacion-y-ppa.md).
// Cada archivo corre dos veces:
//   - ideal: productor y receptor siempre listos; mide L e II (interfaz-rtl.md).
//   - con pausas: burbujas de entrada y out_ready = 0 pseudoaleatorios con semilla
//     fija; los valores no deben cambiar (regla 7).
// En todas las corridas, la salida presentada debe mantenerse hasta su transferencia
// (regla 2). Además, reset en medio de una trama con el arreglo lleno, sin resultado
// pendiente y con un resultado pendiente (regla 6).
// Con +regresion agrega build/vectors/qpsk_s1.txt (generado con python3 -m model.vectors).
module tb_fir_time_systolic;

    localparam int W_IN   = 2;
    localparam int W_OUT  = 9;
    localparam int MAX_N  = 4096;
    localparam int L_ESP  = 1;   // B03, sección 4
    localparam int II_ESP = 1;
    localparam int FIN_ESPERA = 20;  // ciclos sin entrada para detectar resultados extra
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

    fir_time_systolic dut (
        .clk(clk), .rst(rst),
        .in_i(in_i), .in_q(in_q), .in_valid(in_valid), .in_last(in_last), .in_ready(in_ready),
        .out_i(out_i), .out_q(out_q), .out_valid(out_valid), .out_last(out_last), .out_ready(out_ready)
    );

    always #5 clk = ~clk;

    // Vectores del archivo en curso.
    integer v_last [0:MAX_N-1];
    integer v_x_i  [0:MAX_N-1];
    integer v_x_q  [0:MAX_N-1];
    integer v_yt_i [0:MAX_N-1];
    integer v_yt_q [0:MAX_N-1];
    integer n_tot;

    // Estado de la corrida.
    string  archivo;
    logic   corriendo = 0;
    logic   con_pausas = 0;
    integer semilla_in, semilla_out;
    integer n_in, n_out;       // transferencias de entrada y salida
    integer presentada;        // índice de la muestra presentada (-1: ninguna)
    integer ciclo;
    logic   visto;             // out_valid ya visto para el resultado n_out
    logic signed [W_OUT-1:0] ret_i, ret_q;  // salida presentada, para la regla 2
    logic   ret_last;
    integer t_acepta [0:MAX_N-1];
    integer t_valido [0:MAX_N-1];

    // Monitor: detecta transferencias en el flanco, con los valores del ciclo.
    always @(posedge clk) begin
        if (!rst) begin
            ciclo = ciclo + 1;
            if (in_valid && in_ready) begin
                t_acepta[n_in] = ciclo;
                n_in = n_in + 1;
            end
            // Regla 2 en la salida: presentada, no cambia ni se retira hasta la transferencia.
            if (out_valid && !visto) begin
                t_valido[n_out] = ciclo;
                visto    = 1;
                ret_i    = out_i;
                ret_q    = out_q;
                ret_last = out_last;
            end else if (out_valid && (out_i !== ret_i || out_q !== ret_q || out_last !== ret_last)) begin
                $fatal(1, "FALLA time_optimized %s índice %0d: la salida cambió esperando out_ready (regla 2): %0d/%0d last=%0d -> %0d/%0d last=%0d",
                       archivo, n_out, ret_i, ret_q, ret_last, out_i, out_q, out_last);
            end else if (!out_valid && visto) begin
                $fatal(1, "FALLA time_optimized %s índice %0d: out_valid bajó sin transferencia (regla 2)",
                       archivo, n_out);
            end
            if (out_valid && out_ready) begin
                if (n_out >= n_tot)
                    $fatal(1, "FALLA time_optimized %s: resultado extra, índice %0d", archivo, n_out);
                if (out_i !== v_yt_i[n_out] || out_q !== v_yt_q[n_out] || out_last !== (v_last[n_out] != 0))
                    $fatal(1, "FALLA time_optimized %s (pausas=%0d, semilla=%0d) índice %0d: esperado I/Q = %0d/%0d last=%0d, obtenido %0d/%0d last=%0d (enteros Q2.7)",
                           archivo, con_pausas, SEMILLA, n_out,
                           v_yt_i[n_out], v_yt_q[n_out], v_last[n_out] != 0, out_i, out_q, out_last);
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
            if (!in_valid && n_in < n_tot) begin
                if (con_pausas && ($random(semilla_in) % 4 == 0)) begin
                    // burbuja: este ciclo no se presenta muestra
                end else begin
                    in_i       = v_x_i[n_in];
                    in_q       = v_x_q[n_in];
                    in_last    = v_last[n_in] != 0;
                    presentada = n_in;
                    in_valid   = 1;
                end
            end
            out_ready = con_pausas ? ($random(semilla_out) % 3 != 0) : 1;
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
                v_yt_i[n_tot] = yt_i;
                v_yt_q[n_tot] = yt_q;
                n_tot = n_tot + 1;
            end
        end
        $fclose(fd);
        if (n_tot == 0) $fatal(1, "%s: no tiene muestras", ruta);
    endtask

    // Espera todos los resultados de la corrida y comprueba que no sobre ninguno.
    task automatic esperar_fin(input string ruta);
        integer espera;
        espera = 0;
        while (n_out < n_tot) begin
            @(negedge clk);
            espera = espera + 1;
            if (espera > 40 * n_tot + 100)
                $fatal(1, "FALLA time_optimized %s: timeout con %0d de %0d resultados", ruta, n_out, n_tot);
        end

        // Unos ciclos más sin entrada: no debe aparecer ningún resultado extra.
        corriendo = 0;
        in_valid  = 0;
        out_ready = 1;
        repeat (FIN_ESPERA) @(negedge clk);
        if (n_in != n_tot)
            $fatal(1, "FALLA time_optimized %s: %0d muestras aceptadas de %0d", ruta, n_in, n_tot);
    endtask

    // Carga el archivo, resetea el núcleo y arranca productor y receptor.
    task automatic correr_preparar(input string ruta, input logic pausas);
        cargar(ruta);
        archivo     = ruta;
        con_pausas  = pausas;
        semilla_in  = SEMILLA;
        semilla_out = SEMILLA + 1;

        // Reset de dos ciclos; el monitor no cuenta nada mientras rst = 1.
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
        repeat (2) @(negedge clk);
        rst = 0;
        corriendo = 1;
    endtask

    task automatic correr(input string ruta, input logic pausas);
        integer tramas;
        correr_preparar(ruta, pausas);
        esperar_fin(ruta);

        tramas = 0;
        for (int n = 0; n < n_tot; n++) tramas += (v_last[n] != 0);

        if (!pausas) begin
            // L e II con entrada siempre disponible y out_ready = 1 (interfaz-rtl.md).
            for (int n = 0; n < n_tot; n++) begin
                if (t_valido[n] - t_acepta[n] != L_ESP)
                    $fatal(1, "FALLA time_optimized %s: L = %0d en el índice %0d, se esperaba %0d",
                           ruta, t_valido[n] - t_acepta[n], n, L_ESP);
                if (n > 0 && t_acepta[n] - t_acepta[n-1] != II_ESP)
                    $fatal(1, "FALLA time_optimized %s: II = %0d en el índice %0d, se esperaba %0d",
                           ruta, t_acepta[n] - t_acepta[n-1], n, II_ESP);
            end
            $display("OK time_optimized %s ideal: %0d muestras, %0d tramas, L = %0d, II = %0d",
                     ruta, n_tot, tramas, L_ESP, II_ESP);
        end else begin
            $display("OK time_optimized %s con pausas (semilla %0d): %0d muestras en %0d ciclos",
                     ruta, SEMILLA, n_tot, ciclo);
        end
    endtask

    task automatic correr_ambos(input string ruta);
        correr(ruta, 0);
        correr(ruta, 1);
    endtask

    // Regla 6: reset en medio de una trama con las sumas parciales cargadas, sin
    // resultado pendiente (pendiente = 0) o con y[4] esperando out_ready (pendiente = 1).
    // Llena el arreglo con extremos_tiempo (todas las muestras son ±1, sin last en las
    // cinco primeras), resetea y corre impulso.txt sin otro reset: si alguna s_k no
    // quedó en cero, el impulso no coincide; si el resultado pendiente no se canceló,
    // sale un resultado de más.
    task automatic reset_en_trama(input logic pendiente);
        integer n_out_antes;

        // 1) Cinco muestras ±1 aceptadas; después se frena el productor.
        correr_preparar("vectors/extremos_tiempo.txt", 0);
        archivo = pendiente ? "reset con y[4] pendiente (extremos_tiempo)" : "reset con el arreglo lleno (extremos_tiempo)";
        while (n_in < 5) @(negedge clk);
        corriendo = 0;
        in_valid  = 0;
        out_ready = !pendiente;  // con pendiente = 1, y[4] queda esperando
        repeat (3) @(negedge clk);
        if (n_in !== 5 || out_valid !== pendiente || in_ready !== !pendiente)
            $fatal(1, "FALLA time_optimized %s: antes del reset se esperaba n_in = 5, out_valid = %0d e in_ready = %0d; hay %0d, %0d y %0d",
                   archivo, pendiente, !pendiente, n_in, out_valid, in_ready);

        // 2) Reset de un solo flanco, el caso mínimo: con un segundo flanco, un núcleo
        //    que limpia tarde las sumas parciales pasaría igual.
        //    Mientras rst = 1: sin transferencias y con in_ready = out_valid = 0.
        rst   = 1;
        visto = 0;
        n_out_antes = n_out;
        #1;
        if (in_ready !== 0 || out_valid !== 0)
            $fatal(1, "FALLA time_optimized %s: con rst = 1, in_ready = %0d y out_valid = %0d",
                   archivo, in_ready, out_valid);
        @(negedge clk);
        rst = 0;

        // Sin entrada y con el receptor listo, no debe salir el resultado cancelado.
        out_ready = 1;
        repeat (FIN_ESPERA) @(negedge clk);
        if (n_out != n_out_antes)
            $fatal(1, "FALLA time_optimized %s: salió un resultado cancelado por el reset", archivo);

        // 3) impulso.txt sin otro reset: exige sumas parciales en cero (x[n<0] = 0).
        cargar("vectors/impulso.txt");
        archivo    = pendiente ? "vectors/impulso.txt tras reset con y[4] pendiente" : "vectors/impulso.txt tras reset con el arreglo lleno";
        con_pausas = 0;
        n_in       = 0;
        n_out      = 0;
        ciclo      = 0;
        visto      = 0;
        presentada = -1;
        corriendo  = 1;
        esperar_fin(archivo);
        $display("OK time_optimized %s: ningún resultado tras el reset e impulso con sumas parciales en cero", archivo);
    endtask

    initial begin
        correr_ambos("vectors/impulso.txt");
        correr_ambos("vectors/ceros.txt");
        correr_ambos("vectors/extremos_tiempo.txt");
        correr_ambos("vectors/extremos_frecuencia.txt");
        correr_ambos("vectors/bordes.txt");
        reset_en_trama(0);
        reset_en_trama(1);
        if ($test$plusargs("regresion"))
            correr_ambos("build/vectors/qpsk_s1.txt");
        $display("PASS time_optimized: vector matching, L e II, pausas, salida estable y reset en trama");
        $finish;
    end

endmodule
