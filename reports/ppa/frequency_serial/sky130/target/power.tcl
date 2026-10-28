set_cmd_units -time ns -capacitance pF -current mA -voltage V -resistance kOhm -distance um
read_liberty {/mnt/datos/marvell/RTL/rrc-fir-rtl/build/ppa/frequency_serial/20261024T190548892720Z-22dd3d09/sky130_fd_sc_hd__tt_025C_1v80.lib}
read_verilog {/mnt/datos/marvell/RTL/rrc-fir-rtl/build/ppa/frequency_serial/20261024T190548892720Z-22dd3d09/runs/target/51-openroad-fillinsertion/fir_frequency_serial.nl.v}
link_design fir_frequency_serial
read_sdc {/mnt/datos/marvell/RTL/rrc-fir-rtl/build/ppa/frequency_serial/20261024T190548892720Z-22dd3d09/runs/target/51-openroad-fillinsertion/fir_frequency_serial.sdc}
read_spef {/mnt/datos/marvell/RTL/rrc-fir-rtl/build/ppa/frequency_serial/20261024T190548892720Z-22dd3d09/runs/target/53-openroad-rcx/nom/fir_frequency_serial.nom.spef}
set_propagated_clock [all_clocks]
report_parasitic_annotation -report_unannotated
read_vcd -scope {tb_fir_frequency_ppa/dut} {/mnt/datos/marvell/RTL/rrc-fir-rtl/build/ppa/frequency_serial/20261024T190548892720Z-22dd3d09/target/activity.vcd}
report_power -digits 9
set corner [lindex [sta::corners] 0]
puts "PPA_POWER [lrange [sta::design_power $corner] 0 3]"
set matched 0
set unmatched 0
set internal_pins 0
foreach pin [concat [get_pins -hierarchical *] [get_ports *]] {
  if {[get_property $pin direction] eq "internal"} { incr internal_pins; continue }
  set origin [lindex [get_property $pin activity] 2]
  if {$origin in {vcd clock constant}} { incr matched } else {
    incr unmatched
    puts "PPA_UNMATCHED [get_full_name $pin] $origin"
  }
}
puts "PPA_COVERAGE $matched $unmatched"
puts "PPA_INTERNAL_EXCLUDED $internal_pins"
exit
