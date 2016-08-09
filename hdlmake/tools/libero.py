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

"""Module providing support for Microsemi Libero IDE synthesis"""


from .make_syn import ToolSyn
from hdlmake.srcfile import VHDLFile, VerilogFile, SDCFile, PDCFile


class ToolLibero(ToolSyn):

    """Class providing the interface for Microsemi Libero IDE synthesis"""

    TOOL_INFO = {
        'name': 'Libero',
        'id': 'libero',
        'windows_bin': 'libero SCRIPT:',
        'linux_bin': 'libero SCRIPT:',
        'project_ext': 'prjx'}

    STANDARD_LIBS = ['ieee', 'std']

    SUPPORTED_FILES = [SDCFile, PDCFile]

    HDL_FILES = [VHDLFile, VerilogFile]

    CLEAN_TARGETS = {'clean': ["$(PROJECT)", "run.tcl"],
                     'mrproper': ["*.pdb", "*.stp"]}

    TCL_CONTROLS = {
        'create': 'new_project -location {{./{0}}} -name {{{0}}}'
                  ' -hdl {{VHDL}} -family {{ProASIC3}} -die {{{1}}}'
                  ' -package {{{2}}} -speed {{{3}}} -die_voltage {{1.5}}',
        'open': 'open_project -file {$(PROJECT)/$(PROJECT_FILE)}',
        'save': 'save_project',
        'close': 'close_project',
        'synthesize': '',
        'translate': '',
        'map': '',
        'par': '',
        'bitstream':
        'update_and_run_tool -name {GENERATEPROGRAMMINGDATA}',
        'install_source': '$(PROJECT)/designer/impl1/$(SYN_TOP).pdb'}

    def __init__(self):
        super(ToolLibero, self).__init__()
        self._tool_info.update(ToolLibero.TOOL_INFO)
        self._hdl_files.extend(ToolLibero.HDL_FILES)
        self._supported_files.extend(ToolLibero.SUPPORTED_FILES)
        self._clean_targets.update(ToolLibero.CLEAN_TARGETS)
        self._tcl_controls.update(ToolLibero.TCL_CONTROLS)

    def makefile_syn_tcl(self):
        """Create a Libero synthesis project by TCL"""
        syn_project = self.top_module.manifest_dict["syn_project"]
        syn_device = self.top_module.manifest_dict["syn_device"]
        syn_grade = self.top_module.manifest_dict["syn_grade"]
        syn_package = self.top_module.manifest_dict["syn_package"]
        create_tmp = self._tcl_controls["create"]
        self._tcl_controls["create"] = create_tmp.format(syn_project,
                                                         syn_device.upper(),
                                                         syn_package.upper(),
                                                         syn_grade)
        super(ToolLibero, self).makefile_syn_tcl()

    def makefile_syn_files(self):
        """Write the files TCL section of the Makefile"""
        link_string = 'create_links {0} {{{1}}}'
        synthesis_constraints = []
        compilation_constraints = []
        ret = []
        ret.append("define TCL_FILES")
        # First stage: linking files
        for file_aux in self.fileset:
            if (isinstance(file_aux, VHDLFile) or
                    isinstance(file_aux, VerilogFile)):
                line = link_string.format('-hdl_source', file_aux.rel_path())
            elif isinstance(file_aux, SDCFile):
                line = link_string.format('-sdc', file_aux.rel_path())
                synthesis_constraints.append(file_aux)
                compilation_constraints.append(file_aux)
            elif isinstance(file_aux, PDCFile):
                line = link_string.format('-pdc', file_aux.rel_path())
                compilation_constraints.append(file_aux)
            else:
                continue
            ret.append(line)
        # Second stage: Organizing / activating synthesis constraints (the top
        # module needs to be present!)
        if synthesis_constraints:
            line = 'organize_tool_files -tool {SYNTHESIZE} '
            for file_aux in synthesis_constraints:
                line = line + '-file {' + file_aux.rel_path() + '} '
            line = line + \
                '-module {$(TOP_MODULE)::work} -input_type {constraint}'
            ret.append(line)
        # Third stage: Organizing / activating compilation constraints (the top
        # module needs to be present!)
        if compilation_constraints:
            line = 'organize_tool_files -tool {COMPILE} '
            for file_aux in compilation_constraints:
                line = line + '-file {' + file_aux.rel_path() + '} '
            line = line + \
                '-module {$(TOP_MODULE)::work} -input_type {constraint}'
            ret.append(line)
        # Fourth stage: set root/top module
        line = 'set_root -module {$(TOP_MODULE)::work}'
        ret.append(line)
        ret.append("endef")
        ret.append("export TCL_FILES")
        self.writeln('\n'.join(ret))
