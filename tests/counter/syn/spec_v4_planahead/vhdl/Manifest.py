target = "xilinx"
action = "synthesis"

syn_device = "xc6slx45t"
syn_grade = "-3"
syn_package = "fgg484"
syn_top = "spec_top"
syn_project = "demo"
syn_tool = "planahead"

modules = {
  "local" : [ "../../../top/spec_v4/vhdl" ],
}

