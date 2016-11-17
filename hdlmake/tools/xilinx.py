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

"""Module providing generic support for Xilinx synthesis tools"""


from __future__ import absolute_import
from .make_syn import ToolSyn
from hdlmake.srcfile import VHDLFile, VerilogFile, SVFile, TCLFile


class ToolXilinx(ToolSyn):

    """Class providing the interface for Xilinx Vivado synthesis"""

    HDL_FILES = [VHDLFile, VerilogFile, SVFile]

    CLEAN_TARGETS = {'mrproper': ["*.bit", "*.bin"]}

    TCL_CONTROLS = {'create': 'create_project $(PROJECT) ./',
                    'open': 'open_project $(PROJECT_FILE)',
                    'save': '',
                    'close': 'exit',
                    'synthesize': 'reset_run synth_1\n'
                                  'launch_runs synth_1\n'
                                  'wait_on_run synth_1',
                    'translate': '',
                    'map': '',
                    'par': 'reset_run impl_1\n'
                           'launch_runs impl_1\n'
                           'wait_on_run impl_1',
                    'install_source': '$(PROJECT).runs/impl_1/$(SYN_TOP).bit'}

    def __init__(self):
        super(ToolXilinx, self).__init__()
        self._hdl_files.extend(ToolXilinx.HDL_FILES)
        self._clean_targets.update(ToolXilinx.CLEAN_TARGETS)
        self._tcl_controls.update(ToolXilinx.TCL_CONTROLS)

    def makefile_syn_tcl(self):
        """Create a Xilinx synthesis project by TCL"""
        tmp = "set_property {0} {1} [{2}]"
        syn_device = self.top_module.manifest_dict["syn_device"]
        syn_grade = self.top_module.manifest_dict["syn_grade"]
        syn_package = self.top_module.manifest_dict["syn_package"]
        syn_top = self.top_module.manifest_dict["syn_top"]
        create_new = []
        create_new.append(self._tcl_controls["create"])
        properties = [
            ['part', syn_device + syn_package + syn_grade, 'current_project'],
            ['target_language', 'VHDL', 'current_project'],
            ['top', syn_top, 'get_property srcset [current_run]']]
        for prop in properties:
            create_new.append(tmp.format(prop[0], prop[1], prop[2]))
        self._tcl_controls["create"] = "\n".join(create_new)
        super(ToolXilinx, self).makefile_syn_tcl()

    def makefile_syn_files(self):
        """Write the files TCL section of the Makefile"""
        self.writeln("define TCL_FILES")
        tmp = "add_files -norecurse {0}"
        tcl = "source {0}"
        hack = "set_property IS_GLOBAL_INCLUDE 1 [get_files {0}]"
        for file_aux in self.fileset:
            if isinstance(file_aux, TCLFile):
                self.writeln(tcl.format(file_aux.rel_path()))
            else:
                self.writeln(tmp.format(file_aux.rel_path()))
                self.writeln(hack.format(file_aux.rel_path()))
        self.writeln('update_compile_order -fileset sources_1')
        self.writeln('update_compile_order -fileset sim_1')
        self.writeln("endef")
        self.writeln("export TCL_FILES")
