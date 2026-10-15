source [file join [file dirname [info script]] helpers.tcl]
proc check {actual expected} {
    if {$actual ne $expected} {error "Expected '$expected', got '$actual'"}
}
check [ppa_json_number {{"activity_cycles":147200,"throughput":1.3913e5}} activity_cycles] 147200
check [ppa_json_number {{"activity_cycles":147200,"throughput":1.3913e5}} throughput] 1.3913e5
check [ppa_report_number "| Slice LUTs* | 1,234 | 20800 | 5.93 |" {{Slice LUTs} {CLB LUTs}}] 1234
check [ppa_report_number "| Block RAM Tile | 0.5 | 50 | 1.0 |" {{Block RAM Tile}}] 0.5
check [ppa_report_number "| Dynamic (W) | 0.027 |" {{Dynamic (W)}}] 0.027
check [catch {ppa_json_number {{"value":"missing"}} value}] 1
check [catch {ppa_report_number {| New format | n/a |} {{Dynamic (W)}}}] 1
check [info complete [ppa_read [file join [file dirname [info script]] run.tcl]]] 1
set defaults [ppa_options {}]
check [dict get $defaults top] fir_frequency_serial
check [dict get $defaults period_ns] 100
check [dict get $defaults latency_cycles] 559
check [dict get $defaults block_cycles] 575
check [dict get $defaults active_cycles] 147200
set temporal [ppa_options {{C:/resultados PPA/time} -top fir_time_serial -bench tb_fir_time_ppa \
    -period_ns 10.5 -latency_cycles 9 -block_cycles 10 -active_cycles 20480 -vectors vectors/time.txt}]
check [dict get $temporal output] {C:/resultados PPA/time}
check [dict get $temporal top] fir_time_serial
check [dict get $temporal bench] tb_fir_time_ppa
check [dict get $temporal period_ns] 10.5
check [dict get $temporal latency_cycles] 9
check [dict get $temporal block_cycles] 10
check [dict get $temporal active_cycles] 20480
check [dict get $temporal vectors] vectors/time.txt
foreach arguments {
    {-top} {-invalid 1} {-period_ns 0} {-period_ns -1} {-period_ns Inf}
    {-period_ns NaN} {-latency_cycles 1.5} {-block_cycles 0} {-active_cycles bad}
    {-top {bad/name}} {-bench {bad name}}
} {
    check [catch {ppa_options $arguments}] 1
}
set saved_cwd [pwd]
set channel [file tempfile fixture]
close $channel
file delete $fixture
file mkdir $fixture
cd $fixture
check [ppa_diagnostic_report missing.txt] ""
ppa_write diagnosis.txt "Diagnóstico de prueba"
ppa_write timing_critical.rpt "Source: work_reg; Destination: operand_reg"
set diagnostic [ppa_diagnostic_report diagnosis.txt]
check [expr {[string first "Diagnóstico de prueba" $diagnostic] >= 0}] 1
check [expr {[string first "Source: work_reg" $diagnostic] >= 0}] 1
check [expr {[string first "Recursos implementados" $diagnostic] < 0}] 1
ppa_write utilization_hierarchical.rpt "u_engine: 100 LUT"
check [expr {[string first "u_engine: 100 LUT" [ppa_diagnostic_report diagnosis.txt]] >= 0}] 1
cd $saved_cwd
file delete -force $fixture
puts "PASS: Vivado report and benchmark parsers (no Vivado execution)."
