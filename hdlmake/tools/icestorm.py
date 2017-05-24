#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 - 2017 CERN
# Author: Javier D. Garcia Lasheras (jgarcia@gl-research.com)
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

"""Module providing support for the IceStorm flow"""


from __future__ import absolute_import

from .make_syn import ToolSyn
from hdlmake.srcfile import VerilogFile, PCFFile


class ToolIcestorm(ToolSyn):

    """Class providing the interface for IceStorm synthesis"""

    TOOL_INFO = {
        'name': 'IceStorm',
        'id': 'icestorm',
        'windows_bin': None,
        'linux_bin': 'yosys -c',
        'project_ext': ''}

    STANDARD_LIBS = []

    SUPPORTED_FILES = {PCFFile: None}

    HDL_FILES = {VerilogFile: 'read_verilog $(sourcefile)'}

    CLEAN_TARGETS = {'clean': ["$(PROJECT).asc", "$(PROJECT).blif"],
                     'mrproper': ["$(PROJECT).bin"]}

    TCL_CONTROLS = {
        'synthesize': 'yosys -import\n' +
                      'source files.tcl\n' +
                      'synth_ice40 -top $(TOP_MODULE) -blif $(PROJECT).blif',
        'par': 'catch {exec arachne-pnr' +
               ' -d $(SYN_DEVICE)' +
               ' -P $(SYN_PACKAGE)' +
               ' -p $(SOURCES_PCFFile)' +
               ' -o $(PROJECT).asc' +
               ' $(PROJECT).blif}',
        'bitstream': 'catch {exec icepack $(PROJECT).asc $(PROJECT).bin}',
        'install_source': ''}

    def __init__(self):
        super(ToolIcestorm, self).__init__()
        self._tool_info.update(ToolIcestorm.TOOL_INFO)
        self._hdl_files.update(ToolIcestorm.HDL_FILES)
        self._supported_files.update(ToolIcestorm.SUPPORTED_FILES)
        self._standard_libs.extend(ToolIcestorm.STANDARD_LIBS)
        self._clean_targets.update(ToolIcestorm.CLEAN_TARGETS)
        self._tcl_controls.update(ToolIcestorm.TCL_CONTROLS)

    def _makefile_syn_top(self):
        self.manifest_dict["syn_family"] = 'iCE40'
        super(ToolIcestorm, self)._makefile_syn_top()

