target = "altera"
action = "synthesis"

# Supported families on tools/quartus.py
# Quartus Web only supports the family ep2agx45:
syn_device = "ep2agx45cu"
syn_grade = "c6"
syn_package = "17"
syn_top = "myfilter"
syn_project = "myfilter"
#syn_tool = "quartus"

files = ["../../../modules/fir/myfilter.vhd"]

