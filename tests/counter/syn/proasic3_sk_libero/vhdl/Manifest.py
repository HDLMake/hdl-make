target = "microsemi"
action = "synthesis"

syn_device = "a3p250"
syn_grade = "-2"
syn_package = "208 pqfp"
syn_top = "proasic3_top"
syn_project = "demo"
syn_tool = "libero"

modules = {
  "local" : [ "../../../top/proasic3_sk/vhdl" ],
}


