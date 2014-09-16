target = "altera"
action = "synthesis"

syn_device = "ep3c25"
syn_grade = "c6"
syn_package = "f324"
syn_top = "cyclone3_top"
syn_project = "demo"
syn_tool = "quartus"

quartus_preflow = "../../../top/cyclone3_sk/pinout.tcl"
quartus_postmodule = "../../../top/cyclone3_sk/module.tcl"

modules = {
  "local" : [ "../../../top/cyclone3_sk/vhdl" ],
}

