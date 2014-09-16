target = "lattice"
action = "synthesis"

syn_device = "lfxp2-5e"
syn_grade = "-6"
syn_package = "tn144c"
syn_top = "brevia2_top"
syn_project = "demo"
syn_tool = "diamond"

modules = {
  "local" : [ "../../../top/brevia2_dk/vhdl" ],
}

