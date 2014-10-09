action = "simulation"
include_dirs = [ "../environment/",
                 "../sequences/"]

vlog_opt = '+incdir+' + \
           '../../mvc//questa_mvc_src/sv+' + \
           '../../mvc/questa_mvc_src/sv/mvc_base+' + \
           '../../mvc/include+' +\
           '../../uvm-1.1d/src'
                
top_module = "top"
sim_tool = "vsim"

files = ["src/genericTest.sv"]

modules = { "local" : ["../../rtl"] }
