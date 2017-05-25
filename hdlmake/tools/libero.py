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


from __future__ import absolute_import
from .make_syn import ToolSyn
from hdlmake.srcfile import VHDLFile, VerilogFile, SDCFile, PDCFile


class ToolLibero(ToolSyn):

    """Class providing the interface for Microsemi Libero IDE synthesis"""

    TOOL_INFO = {
        'name': 'Libero',
        'id': 'libero',
        'windows_bin': 'libero.exe SCRIPT:',
        'linux_bin': 'libero SCRIPT:',
        'project_ext': 'prjx'}

    STANDARD_LIBS = ['ieee', 'std']

    _LIBERO_SOURCE = 'create_links {0} {{$$filename}}'

    SUPPORTED_FILES = {
        SDCFile: _LIBERO_SOURCE.format('-sdc'),
        PDCFile: _LIBERO_SOURCE.format('-pdc')}

    HDL_FILES = {
        VHDLFile: _LIBERO_SOURCE.format('-hdl_source'),
        VerilogFile: _LIBERO_SOURCE.format('-hdl_source')}

    CLEAN_TARGETS = {'clean': ["$(PROJECT)"],
                     'mrproper': ["*.pdb", "*.stp"]}

    TCL_CONTROLS = {
        'create': 'new_project -location {{./{0}}} -name {{{0}}}'
                  ' -hdl {{VHDL}} -family {{ProASIC3}} -die {{{1}}}'
                  ' -package {{{2}}} -speed {{{3}}} -die_voltage {{1.5}}',
        'open': 'open_project -file {$(PROJECT)/$(PROJECT_FILE)}',
        'save': 'save_project',
        'close': 'close_project',
        'project': '$(TCL_CREATE)\n'
                   '$(TCL_FILES)\n'
                   '{0}\n'
                   '$(TCL_SAVE)\n'
                   '$(TCL_CLOSE)',
        'bitstream': '$(TCL_OPEN)\n'
                     'update_and_run_tool'
                     ' -name {GENERATEPROGRAMMINGDATA}\n'
                     '$(TCL_SAVE)\n'
                     '$(TCL_CLOSE)',
        'install_source': '$(PROJECT)/designer/impl1/$(SYN_TOP).pdb'}

    def __init__(self):
        super(ToolLibero, self).__init__()
        self._tool_info.update(ToolLibero.TOOL_INFO)
        self._hdl_files.update(ToolLibero.HDL_FILES)
        self._supported_files.update(ToolLibero.SUPPORTED_FILES)
        self._standard_libs.extend(ToolLibero.STANDARD_LIBS)
        self._clean_targets.update(ToolLibero.CLEAN_TARGETS)
        self._tcl_controls.update(ToolLibero.TCL_CONTROLS)

    def _makefile_syn_tcl(self):
        """Create a Libero synthesis project by TCL"""
        syn_project = self.manifest_dict["syn_project"]
        syn_device = self.manifest_dict["syn_device"]
        syn_grade = self.manifest_dict["syn_grade"]
        syn_package = self.manifest_dict["syn_package"]
        create_tmp = self._tcl_controls["create"]
        self._tcl_controls["create"] = create_tmp.format(syn_project,
                                                         syn_device.upper(),
                                                         syn_package.upper(),
                                                         syn_grade)
        project_tmp = self._tcl_controls["project"]
        synthesis_constraints = []
        compilation_constraints = []
        ret = []
        # First stage: linking files
        for file_aux in self.fileset:
            if isinstance(file_aux, SDCFile):
                synthesis_constraints.append(file_aux)
                compilation_constraints.append(file_aux)
            elif isinstance(file_aux, PDCFile):
                compilation_constraints.append(file_aux)
            else:
                continue
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
        self._tcl_controls['project'] = project_tmp.format('\n'.join(ret))
        super(ToolLibero, self)._makefile_syn_tcl()
