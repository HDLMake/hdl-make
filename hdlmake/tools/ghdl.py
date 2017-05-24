#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 - 2015 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Multi-tool support by Javier D. Garcia-Lasheras (javier@garcialasheras.com)
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

"""Module providing support for GHDL simulator"""

from __future__ import absolute_import
import string

from .make_sim import ToolSim
from hdlmake.srcfile import VHDLFile


class ToolGHDL(ToolSim):

    """Class providing the interface for GHDL simulator"""

    TOOL_INFO = {
        'name': 'GHDL',
        'id': 'ghdl',
        'windows_bin': None,
        'linux_bin': 'ghdl'}

    STANDARD_LIBS = ['ieee', 'std']

    HDL_FILES = {VHDLFile: ''}

    CLEAN_TARGETS = {'clean': ["*.cf", "*.o", "$(TOP_MODULE)", "work"],
                     'mrproper': ["*.vcd"]}

    SIMULATOR_CONTROLS = {'vlog': None,
                          'vhdl': 'ghdl -a $<',
                          'compiler': 'ghdl -e $(TOP_MODULE)'}

    def __init__(self):
        super(ToolGHDL, self).__init__()
        self._tool_info.update(ToolGHDL.TOOL_INFO)
        self._hdl_files.update(ToolGHDL.HDL_FILES)
        self._standard_libs.extend(ToolGHDL.STANDARD_LIBS)
        self._clean_targets.update(ToolGHDL.CLEAN_TARGETS)
        self._simulator_controls.update(ToolGHDL.SIMULATOR_CONTROLS)

    def _makefile_sim_options(self):
        """Print the GHDL options to the Makefile"""
        ghdl_opt = self.manifest_dict.get("ghdl_opt", '')
        ghdl_string = string.Template(
            """GHDL_OPT := ${ghdl_opt}\n""")
        self.writeln(ghdl_string.substitute(
            ghdl_opt=ghdl_opt))

    def _makefile_sim_compilation(self):
        """Print the GDHL simulation compilation target"""
        self.writeln("simulation: $(VERILOG_OBJ) $(VHDL_OBJ)")
        self.writeln("\t\t" + self._simulator_controls['compiler'])
        self.writeln('\n')
        self._makefile_sim_dep_files()
