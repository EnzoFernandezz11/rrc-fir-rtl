# Vivado batch entry point; run.bat [new_output_directory].
set script_dir [file dirname [file normalize [info script]]]
source [file join $script_dir helpers.tcl]
set root [file normalize [file join $script_dir ../../..]]
if {[llength $argv] > 1} {error "Usage: run.bat \[new_output_directory\]"}
set source_id source
if {[file exists [file join $root manifest.json]] &&
    [regexp {"commit"\s*:\s*"([0-9a-f]{7,40})"} [ppa_read [file join $root manifest.json]] -> commit]} {
    set source_id [string range $commit 0 7]
}
set run_id "[clock format [clock seconds] -gmt 1 -format %Y%m%dT%H%M%SZ]-${source_id}-vivado"
set output [file join $root build ppa frequency_serial $run_id]
if {[llength $argv]} {set output [file normalize [lindex $argv 0]]}
set launched [expr {[info exists ::env(PPA_VIVADO_OUTPUT)] &&
    [file normalize $::env(PPA_VIVADO_OUTPUT)] eq $output &&
    [file exists [file join $output launch_pending.txt]]}]
if {[file exists $output] && !$launched} {error "Output already exists; choose a new directory: $output"}
file mkdir $output
if {$launched} {file delete [file join $output launch_pending.txt]}
cd $output
ppa_write run_status.txt RUNNING

proc ppa_main {root script_dir output} {
    set part xc7a35tcpg236-1
    set top fir_frequency_serial
    set bench tb_fir_frequency_ppa
    set vectors [file join $root vectors ppa_vectors.txt]
    set tb [file join $root tb frequency ${bench}.sv]
    set constraint [file join $root constraints clk_10mhz.xdc]
    set diagnosis [file join $root diagnosis.txt]
    set rtl [lsort [glob [file join $root rtl frequency *.sv]]]
    foreach path [concat $rtl [list $vectors $tb $constraint $diagnosis]] {
        if {![file isfile $path]} {error "Required input missing: $path"}
    }
    if {![info exists ::env(XILINX_VIVADO)]} {error "XILINX_VIVADO is unset; use settings64.bat"}
    ppa_write tool_versions.txt [version]
    ppa_write configuration.txt "top=$top\npart=$part\nclock_period_ns=100\nmode=out_of_context\nstrategies=default\nsdf_corner=slow\nsdf_column=max\nseed=1\nsymbols=1024\nsamples=2048\noperating_conditions=Vivado defaults; see operating_conditions.rpt\nsource_root=$root"
    foreach manifest {manifest.json package_manifest.json} {
        if {[file exists [file join $root $manifest]]} {
            file copy [file join $root $manifest] [file join $output source_$manifest]
        }
    }

    read_verilog -sv $rtl
    read_xdc $constraint
    synth_design -top $top -part $part -mode out_of_context
    if {[llength [get_clocks clk]] != 1 || [get_property PERIOD [get_clocks clk]] != 100.0} {
        error "Expected one clk constraint with 100 ns period"
    }
    opt_design
    place_design
    route_design
    write_checkpoint implemented.dcp
    write_xdc implemented.xdc
    report_utilization -file utilization.rpt
    report_utilization -hierarchical -file utilization_hierarchical.rpt
    report_timing_summary -delay_type min_max -report_unconstrained -file timing_summary.rpt
    report_timing -from [get_clocks clk] -to [get_clocks clk] -delay_type max -max_paths 10 -file timing_setup.rpt
    report_timing -from [get_clocks clk] -to [get_clocks clk] -delay_type max -max_paths 1 -path_type full -input_pins -file timing_critical.rpt
    report_timing -from [get_clocks clk] -to [get_clocks clk] -delay_type min -max_paths 10 -file timing_hold.rpt
    check_timing -verbose -file check_timing.rpt
    report_route_status -file route_status.rpt
    report_drc -file drc.rpt
    set setup [get_timing_paths -from [get_clocks clk] -to [get_clocks clk] -delay_type max -max_paths 1]
    set hold [get_timing_paths -from [get_clocks clk] -to [get_clocks clk] -delay_type min -max_paths 1]
    if {[llength $setup] != 1 || [llength $hold] != 1} {error "Internal clock timing paths missing"}
    set wns [get_property SLACK $setup]
    set whs [get_property SLACK $hold]
    if {$wns >= 100} {error "Invalid setup slack for Fmax estimate: $wns"}
    set fmax [expr {1000.0 / (100.0 - $wns)}]

    # Annotation is explicit at xelab; avoid double annotation in the netlist.
    write_verilog -mode timesim -sdf_anno false implemented.v
    write_sdf -process_corner slow implemented.sdf
    ppa_exec xvlog_console.log xvlog --sv --work xil_defaultlib implemented.v $tb [file join $::env(XILINX_VIVADO) data verilog src glbl.v]
    ppa_exec xelab_console.log xelab -debug typical -L simprims_ver -L secureip \
        -transport_int_delays -pulse_r 0 -pulse_int_r 0 \
        -sdfmax /${bench}/dut=implemented.sdf xil_defaultlib.$bench xil_defaultlib.glbl -s ppa_timing
    ppa_exec xsim_console.log xsim ppa_timing -tclbatch [file join $script_dir simulate.tcl] \
        -testplusarg VECTORS=$vectors -testplusarg METRICS=timing_metrics.json -testplusarg TIMING \
        -onfinish stop -onerror stop
    foreach evidence {simulation_passed.txt timing_metrics.json activity.saif} {
        if {![file exists $evidence] || [file size $evidence] == 0} {error "Simulation incomplete: $evidence missing"}
    }
    set metrics [ppa_read timing_metrics.json]
    set samples [ppa_json_number $metrics output_samples]
    set throughput [ppa_json_number $metrics throughput_samples_per_second]
    set active [ppa_json_number $metrics active_cycles]
    set latency [ppa_json_number $metrics latency_cycles]
    set block [ppa_json_number $metrics block_cycles]
    if {$samples != 2048 || $active != 147200 || $latency != 559 || $block != 575 || $throughput <= 0} {
        error "Post-route benchmark metrics differ from the agreed workload"
    }
    puts "PPA_SAIF_BEGIN"
    read_saif -strip_path tb_fir_frequency_ppa/dut -out_file unmatched_saif.rpt activity.saif
    puts "PPA_SAIF_END"
    report_switching_activity -file switching_activity.rpt [get_nets -hierarchical]
    report_operating_conditions -file operating_conditions.rpt
    report_power -file power.rpt
    set saif_summary "Consultar la seccion PPA_SAIF_BEGIN / PPA_SAIF_END de vivado.log."
    if {[file exists vivado.log]} {
        regexp {(?s)\nPPA_SAIF_BEGIN\r?\n(.*?)\r?\nPPA_SAIF_END} [ppa_read vivado.log] -> saif_summary
    }
    ppa_write read_saif.rpt $saif_summary
    set utilization [ppa_read utilization.rpt]
    set lut [ppa_report_number $utilization {{Slice LUTs} {CLB LUTs}}]
    set ff [ppa_report_number $utilization {{Slice Registers} {CLB Registers}}]
    set dsp [ppa_report_number $utilization {{DSPs} {DSP48E1}}]
    set bram [ppa_report_number $utilization {{Block RAM Tile}}]
    set power [ppa_read power.rpt]
    set dynamic [ppa_report_number $power {{Dynamic (W)}}]
    set static [ppa_report_number $power {{Device Static (W)}}]
    set energy [expr {$dynamic / $throughput * 1e9}]
    set timing_status [expr {$wns >= 0 && $whs >= 0 ? "PASS" : "FAIL"}]
    # Report provenance per net; official matching summary remains in read_saif.rpt.
    set reported 0
    set annotated 0
    foreach line [split [ppa_read switching_activity.rpt] \n] {
        if {[string first "static probability" $line] >= 0} {
            incr reported
            if {[string first "(S)" $line] >= 0} {incr annotated}
        }
    }
    set coverage "REVISAR read_saif.rpt y unmatched_saif.rpt"
    if {$reported > 0} {set coverage "$annotated / $reported filas de redes con fuente SAIF (S); revisar correspondencia oficial"}
    ppa_write summary.tsv "metric\tvalue\npart\t$part\nclock_period_ns\t100\ninternal_wns_ns\t$wns\ninternal_whs_ns\t$whs\nfmax_estimate_mhz\t$fmax\nlut\t$lut\nff\t$ff\ndsp\t$dsp\nbram_tiles\t$bram\noutput_samples\t$samples\nactive_cycles\t$active\nlatency_cycles\t$latency\nblock_cycles\t$block\nthroughput_samples_per_second\t$throughput\ndynamic_power_w\t$dynamic\nstatic_power_w\t$static\nenergy_dynamic_nj_per_sample\t$energy\ntiming_status\t$timing_status\nsaif_review\t$coverage"
    set summary "# PPA frequency serial: resultados Vivado\n\nCorrida: [file tail $output]. Vivado: [version -short].\n\nArtix-7 $part; OOC; reloj 10 MHz (100 ns); estrategias por defecto. Benchmark A04, QPSK 2x, semilla 1, 1024 simbolos y 2048 muestras.\n\n| Metrica | Resultado |\n|---|---:|\n| Simulacion temporal, 2048 muestras exactas | PASS |\n| Timing interno setup + hold a 10 MHz | $timing_status |\n| WNS interno (ns) | $wns |\n| WHS interno (ns) | $whs |\n| Fmax estimada (MHz) | [format %.3f $fmax] |\n| LUT | $lut |\n| FF | $ff |\n| DSP | $dsp |\n| BRAM (tiles) | $bram |\n| Latencia (ciclos) | $latency |\n| Ciclos por bloque | $block |\n| Throughput (muestras/s) | [format %.3f $throughput] |\n| Potencia dinamica estimada (W) | $dynamic |\n| Potencia estatica del dispositivo (W) | $static |\n| Energia dinamica (nJ/muestra) | [format %.3f $energy] |\n\nFmax = 1000 / (100 - WNS), estimacion sin barrido. Constraints cubren el reloj interno; la integracion fisica y los tiempos de entrada/salida requieren constraints del sistema. Ver check_timing.rpt y timing_summary.rpt. La estatica corresponde al dispositivo, no solo al nucleo.\n\nSAIF: $coverage. La potencia requiere revisar la cobertura; las redes sin anotacion pueden usar actividad estimada. Ventana SAIF: 147200 ciclos, excluye reset y guarda final; incluye copia, captura, calculo y emision. Simulacion SDF slow/max; STA reporta setup y hold.\n\n## Correspondencia SAIF\n\n```text\n[ppa_read read_saif.rpt]\n```\n\n## Condiciones de potencia\n\nSe conservaron los valores por defecto de esta version y dispositivo:\n\n```text\n[ppa_read operating_conditions.rpt]\n```\n\n## Evidencia\n\nReportes: utilization.rpt, utilization_hierarchical.rpt, timing_setup.rpt, timing_hold.rpt, power.rpt, unmatched_saif.rpt, switching_activity.rpt. Simulacion: timing_metrics.json, xelab_console.log, xsim_console.log y activity.saif. Implementacion: implemented.dcp, implemented.v y implemented.sdf. Origen: source_manifest.json cuando existe; configuracion y version en configuration.txt y tool_versions.txt.\n"
    append summary [ppa_diagnostic_report $diagnosis]
    set local_report [file join $root summary.md]
    if {[file exists $local_report]} {
        append summary "\n## Referencia local anterior\n\nEl estado pendiente de Vivado en esta referencia describe la corrida local previa; los resultados actuales estan arriba.\n\n[ppa_read $local_report]"
    }
    ppa_write summary.md $summary
    ppa_write run_status.txt "SIMULATION_PASS TIMING_$timing_status POWER_SAIF_REVIEW_REQUIRED"
    puts "Readable results: [file join $output summary.md]"
    if {$timing_status ne "PASS"} {error "Timing failed; inspect summary.md and timing reports"}
}

if {[catch {ppa_main $root $script_dir $output} message options]} {
    ppa_write run_status.txt "FAILED\n$message"
    ppa_write failure.txt [dict get $options -errorinfo]
    if {![file exists summary.md]} {
        set failed_summary "# PPA frequency serial: corrida incompleta\n\nLa corrida fallo: $message\n\nNo se declaran resultados PPA completos. Revisar failure.txt y los reportes generados en esta carpeta.\n\nOrigen: $root\nResultados: $output"
        append failed_summary [ppa_diagnostic_report [file join $root diagnosis.txt]]
        ppa_write summary.md $failed_summary
    }
    ppa_write file_sizes.tsv "file\tbytes\n[ppa_inventory $output]"
    puts stderr "PPA failed: $message\nEvidence: $output"
    exit 1
}
ppa_write file_sizes.tsv "file\tbytes\n[ppa_inventory $output]"
exit 0
