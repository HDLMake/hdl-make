#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 - 2015 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Multi-tool support by Javier D. Garcia-Lasheras (javier@garcialasheras.com)
# Riviera tool added by Josh Smith (joshrsmith@gmail.com)
#
# This file is part of Hdlmake.
#
# Hdlmake is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hdlmake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Hdlmake.  If not, see <http://www.gnu.org/licenses/>.
#

"""Module providing support for Aldec Riviera-PRO simulation"""

from __future__ import print_function
from .sim_makefile_support import VsimMakefileWriter

# as of 2014.06, these are the standard libraries
# included in an installation
RIVIERA_STANDARD_LIBS = [
    'ieee', 'std', 'cpld',
    'vl', 'vital95', 'vital2000',
    'synopsys', 'aldec', 'vtl',
    'vtl_dbg', 'assertions', 'ieee_proposed',
    'ovm_2_0_3', 'ovm_2_1_2', 'uvm_1_0p1',
    'uvm_1_1d', 'uvm', 'osvvm',
]

# there are many vendor specific libraries available
# a few of them are listed here
RIVIERA_XILINX_VHDL_LIBRARIES = [
    'cpld',
    'secureip',
    'simprim',
    'unimacro',
    'unisim',
    'xilinxcorelib'
]
RIVIERA_XILINX_VLOG_LIBRARIES = [
    'cpld_ver',
    'secureip',
    'simprims_ver',
    'uni9000_ver',
    'unimacro_ver',
    'unisims_ver',
    'xilinxcorelib_ver'
]

RIVIERA_STANDARD_LIBS.extend(RIVIERA_XILINX_VHDL_LIBRARIES)
RIVIERA_STANDARD_LIBS.extend(RIVIERA_XILINX_VLOG_LIBRARIES)


class ToolRiviera(VsimMakefileWriter):

    """Class providing the interface for Aldec Riviera-PRO simulator"""

    TOOL_INFO = {
        'name': 'Riviera',
        'id': 'riviera',
        'windows_bin': 'vsim.exe',
        'linux_bin': 'vsim'}

    STANDARD_LIBS = RIVIERA_STANDARD_LIBS

    CLEAN_TARGETS = {'clean': ["*.asdb"],
                     'mrproper': ["*.vcd"]}

    def __init__(self):
        super(ToolRiviera, self).__init__()
        self._tool_info.update(ToolRiviera.TOOL_INFO)
        self._standard_libs.extend(ToolRiviera.STANDARD_LIBS)
        self._clean_targets.update(ToolRiviera.CLEAN_TARGETS)

    def _makefile_sim_options(self):
        """Print the Riviera options to the Makefile"""
        vcom_opt = self.manifest_dict.get("vcom_opt", '')
        self.manifest_dict["vcom_opt"] = "-2008 " + vcom_opt
        super(ToolRiviera, self)._makefile_sim_options()
