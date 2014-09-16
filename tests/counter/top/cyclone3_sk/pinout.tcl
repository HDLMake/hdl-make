
post_message "Assigning pinout"

# Load Quartus II Tcl Project package
package require ::quartus::project

project_open -revision demo demo

set_location_assignment PIN_F1 -to clear_i
set_location_assignment PIN_F2 -to count_i
set_location_assignment PIN_B9 -to clock_i
set_location_assignment PIN_N9 -to led_o[3]
set_location_assignment PIN_N12 -to led_o[2]
set_location_assignment PIN_P12 -to led_o[1]
set_location_assignment PIN_P13 -to led_o[0]

# Commit assignments
export_assignments
project_close

