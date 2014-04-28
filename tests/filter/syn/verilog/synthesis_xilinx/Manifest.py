target = "xilinx"
action = "synthesis"

syn_device = "xc6slx45t"
syn_grade = "-3"
syn_package = "fgg484"
syn_top = "half2"
syn_project = "half2.xise"
syn_tool = "ise"

files = [
    "../../../modules/filtdec/half2.v",
    "../../../modules/filtdec/reg_delay.v"
]

