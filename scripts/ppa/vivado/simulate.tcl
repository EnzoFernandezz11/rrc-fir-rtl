# Invoked by standalone xsim from the run directory. No waveform DB logging.
# The generated simulate_run.tcl supplies the selected benchmark scope.
set start [add_condition -name ppa_start "$tb/activity_window == 1" {stop}]
run "$guard_ns ns"
if {[get_value -radix unsigned $tb/activity_window] ne "1"} {
    error "Benchmark did not start after reset"
}
remove_conditions $start
open_saif activity.saif
log_saif [get_objects -r $tb/dut/*]
set end [add_condition -name ppa_end "$tb/activity_window == 0" {stop}]
run "$active_timeout_ns ns"
close_saif
if {[get_value -radix unsigned $tb/activity_window] ne "0"} {
    error "Benchmark activity window timed out"
}
remove_conditions $end
set done [add_condition -name ppa_done "$tb/benchmark_done == 1" {stop}]
run "$guard_ns ns"
if {[get_value -radix unsigned $tb/benchmark_done] ne "1" ||
    [get_value -radix unsigned $tb/benchmark_pass] ne "1"} {
    error "Post-route benchmark did not pass"
}
set fh [open simulation_passed.txt w]
puts $fh "PASS: all expected samples checked; SAIF excludes reset and guard cycles."
close $fh
quit
