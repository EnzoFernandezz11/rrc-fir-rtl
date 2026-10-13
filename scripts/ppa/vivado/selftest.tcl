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
