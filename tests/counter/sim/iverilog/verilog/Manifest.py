action = "simulation"
sim_tool = "iverilog"
top_module = "counter_tb"

sim_post_cmd = "vvp counter_tb.vvp; gtkwave counter_tb.vcd"

modules = {
  "local" : [ "../../../testbench/counter_tb/verilog" ],
}

