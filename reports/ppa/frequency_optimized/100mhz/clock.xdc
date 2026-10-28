create_clock -name clk -period 10 [get_ports clk]
set_input_delay -clock clk 5.0 [get_ports -filter {DIRECTION == IN && NAME != clk}]
set_output_delay -clock clk 0 [all_outputs]
