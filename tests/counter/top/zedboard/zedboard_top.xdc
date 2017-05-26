# ----------------------------------------------------------------------------
# Clock Source - Bank 13
# ---------------------------------------------------------------------------- 
set_property PACKAGE_PIN Y9 [get_ports clock_i]
set_property IOSTANDARD LVCMOS33 [get_ports clock_i]
create_clock -add -name sys_clk_pin -period 8.00 -waveform {0 4} [get_ports clock_i]


# ----------------------------------------------------------------------------
# Reset - BTNC (user button center)
# ----------------------------------------------------------------------------
set_property PACKAGE_PIN P16 [get_ports {clear_i}]
set_property IOSTANDARD LVCMOS33 [get_ports {clear_i}]


# ----------------------------------------------------------------------------
# Count - BTNU (user button up)
# ----------------------------------------------------------------------------
set_property PACKAGE_PIN T18 [get_ports {count_i}]
set_property IOSTANDARD LVCMOS33 [get_ports {count_i}]


# ----------------------------------------------------------------------------
# USER LEDs
# ---------------------------------------------------------------------------- 
set_property PACKAGE_PIN T22 [get_ports "led_o[0]"]
set_property IOSTANDARD LVCMOS33 [get_ports "led_o[0]"]
set_property PACKAGE_PIN T21 [get_ports "led_o[1]"]
set_property IOSTANDARD LVCMOS33 [get_ports "led_o[1]"]
set_property PACKAGE_PIN U22 [get_ports "led_o[2]"]
set_property IOSTANDARD LVCMOS33 [get_ports "led_o[2]"]
set_property PACKAGE_PIN U21 [get_ports "led_o[3]"]
set_property IOSTANDARD LVCMOS33 [get_ports "led_o[3]"]
set_property PACKAGE_PIN V22 [get_ports "led_o[4]"]
set_property IOSTANDARD LVCMOS33 [get_ports "led_o[4]"]
set_property PACKAGE_PIN W22 [get_ports "led_o[5]"]
set_property IOSTANDARD LVCMOS33 [get_ports "led_o[5]"]
set_property PACKAGE_PIN U19 [get_ports "led_o[6]"]
set_property IOSTANDARD LVCMOS33 [get_ports "led_o[6]"]
set_property PACKAGE_PIN U14 [get_ports "led_o[7]"]
set_property IOSTANDARD LVCMOS33 [get_ports "led_o[7]"]
