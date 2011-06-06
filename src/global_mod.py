#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 Pawel Szostek (pawel.szostek@cern.ch)
#
#    This source code is free software; you can redistribute it
#    and/or modify it in source code form under the terms of the GNU
#    General Public License as published by the Free Software
#    Foundation; either version 2 of the License, or (at your option)
#    any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA
#


options = None
t0 = None
ssh = None
top_module = None
global_target = "''"
modules_pool = None
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
