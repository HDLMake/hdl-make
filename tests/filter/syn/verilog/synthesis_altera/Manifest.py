target = "altera"
action = "synthesis"

# Supported families on tools/quartus.py
# Quartus Web only supports the family ep2agx45:
syn_device = "ep2agx45cu"
syn_grade = "c6"
syn_package = "17"
syn_top = "half2"
syn_project = "half2"
#syn_tool = "quartus"

files = [
    "../../../modules/filtdec/half2.v",
    "../../../modules/filtdec/reg_delay.v"
]

