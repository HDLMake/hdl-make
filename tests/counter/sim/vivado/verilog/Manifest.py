action = "simulation"
sim_tool = "vivado"
sim_top = "counter_tb"

sim_post_cmd = "xsim %s -gui" % sim_top

modules = {
  "local" : [ "../../../testbench/counter_tb/verilog" ],
}
