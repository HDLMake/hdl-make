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
        'windows_bin': 'yosys -c',
        'linux_bin': 'yosys -c',
        'project_ext': ''}

    STANDARD_LIBS = []

    SUPPORTED_FILES = [PCFFile]

    HDL_FILES = [VerilogFile]

    CLEAN_TARGETS = {'clean': ["$(PROJECT).asc", "$(PROJECT).blif"],
                     'mrproper': ["$(PROJECT).bin"]}

    TCL_CONTROLS = {
        'create': '',
        'open': '',
        'save': '',
        'close': '',
        'synthesize': '',
        'translate': '',
        'map': '',
        'par': 'catch {{exec arachne-pnr' +
               ' -d {0}' +
               ' -P {1}' +
               ' -p {2}' +
               ' -o $(PROJECT).asc' +
               ' $(PROJECT).blif}}',
        'bitstream': 'catch {exec icepack $(PROJECT).asc $(PROJECT).bin}',
        'install_source': ''}

    def __init__(self):
        super(ToolIcestorm, self).__init__()
        self._tool_info.update(ToolIcestorm.TOOL_INFO)
        self._hdl_files.extend(ToolIcestorm.HDL_FILES)
        self._supported_files.extend(ToolIcestorm.SUPPORTED_FILES)
        self._standard_libs.extend(ToolIcestorm.STANDARD_LIBS)
        self._clean_targets.update(ToolIcestorm.CLEAN_TARGETS)
        self._tcl_controls.update(ToolIcestorm.TCL_CONTROLS)

    def makefile_syn_files(self):
        """Write the files TCL section of the Makefile"""
        ret = []
        ret.append("define TCL_FILES")
        ret.append("yosys -import")
        # First stage: linking files
        for file_aux in self.fileset:
            if (isinstance(file_aux, VerilogFile)):
                ret.append('read_verilog {0}'.format(file_aux.rel_path()))
        ret.append("synth_ice40 -top {0} -blif {1}.blif".format(
            self.manifest_dict["syn_top"],
            self.manifest_dict["syn_project"]))
        ret.append("endef")
        ret.append("export TCL_FILES")
        self.writeln('\n'.join(ret))

    def makefile_syn_tcl(self):
        """Create an IceStorm synthesis project by TCL"""
        syn_device = self.manifest_dict["syn_device"]
        syn_grade = self.manifest_dict["syn_grade"]
        syn_package = self.manifest_dict["syn_package"]
        syn_properties = self.manifest_dict.get("syn_properties")
        constraints_file = None
        for file_aux in self.fileset:
            if (isinstance(file_aux, PCFFile)):
                constraints_file = file_aux.rel_path()
        if constraints_file == None:
            logging.error("No Arachne-pnr constraints file found!")
            quit()
        tmp = self._tcl_controls["par"]
        self._tcl_controls["par"] = tmp.format(
            syn_device, syn_package, constraints_file)
        super(ToolIcestorm, self).makefile_syn_tcl()

