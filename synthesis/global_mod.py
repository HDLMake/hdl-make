#!/usr/bin/python
# -*- coding: utf-8 -*-

options = None
t0 = None
ssh = None
synth_user = None
synth_server = None
top_manifest = None
cwd = None
opt_map = None
hdlm_path = "hdl_make"
ise_list_makefile = ".Makefile_list"
ise_list_file = "ise_list"

ise_path_64 = {
"10.0":"/opt/Xilinx/10.1/ISE/bin/lin",
"12.2":"/opt/Xilinx/12.2/ISE_DS/ISE/bin/lin64",
"12.1":"/opt/Xilinx/12.1/ISE_DS/ISE/bin/lin",
"12.4":"/opt/Xilinx/12.4/ISE_DS/ISE/bin/lin64",
"13.1":"/opt/Xilinx/13.1/ISE_DS/ISE/bin/lin64"
}

ise_path_32 = {"10.0":"/opt/Xilinx/10.1/ISE/bin/lin",
"12.2":"/opt/Xilinx/12.2/ISE_DS/ISE/bin/lin64",
"12.1":"/opt/Xilinx/12.1/ISE_DS/ISE/bin/lin",
"12.4":"/opt/Xilinx/12.4/ISE_DS/ISE/bin/lin64",
"13.1":"/opt/Xilinx/13.1/ISE_DS/ISE/bin/lin64"}
