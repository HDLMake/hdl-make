action = "simulation"
sim_tool = "aldec"
top_module = "counter_tb"

sim_post_cmd = "vsimsa -do ../play_sim.do; avhdl wave.asdb"

modules = {
  "local" : [ "../../../testbench/counter_tb/verilog" ],
}

