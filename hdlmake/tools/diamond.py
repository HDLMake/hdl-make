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

"""Module providing support for Lattice Diamond IDE"""


from .make_syn import ToolSyn
from hdlmake.srcfile import EDFFile, LPFFile, VHDLFile, VerilogFile

DIAMOND_STANDARD_LIBS = ['ieee', 'std']


class ToolDiamond(ToolSyn):

    """Class providing the interface for Lattice Diamond synthesis"""

    TOOL_INFO = {
        'name': 'Diamond',
        'id': 'diamond',
        'windows_bin': 'pnmainc ',
        'linux_bin': 'diamondc ',
        'project_ext': 'ldf'}

    SUPPORTED_FILES = [EDFFile, LPFFile]

    HDL_FILES = [VHDLFile, VerilogFile]

    CLEAN_TARGETS = {'clean': ["*.sty", "$(PROJECT)", "run.tcl"],
                     'mrproper': ["*.jed"]}

    TCL_CONTROLS = {'create': 'prj_project new -name $(PROJECT)'
                              ' -impl $(PROJECT)'
                              ' -dev {0} -synthesis \"synplify\"',
                    'open': 'prj_project open $(PROJECT).ldf',
                    'save': 'prj_project save',
                    'close': 'prj_project close',
                    'synthesize': '',
                    'translate': '',
                    'map': '',
                    'par': 'prj_run PAR -impl $(PROJECT)',
                    'bitstream':
                    'prj_run Export -impl $(PROJECT) -task Bitgen',
                    'install_source': '$(PROJECT)/$(PROJECT)_$(PROJECT).jed'}

    def __init__(self):
        super(ToolDiamond, self).__init__()
        self._tool_info.update(ToolDiamond.TOOL_INFO)
        self._hdl_files.extend(ToolDiamond.HDL_FILES)
        self._supported_files.extend(ToolDiamond.SUPPORTED_FILES)
        self._clean_targets.update(ToolDiamond.CLEAN_TARGETS)
        self._tcl_controls.update(ToolDiamond.TCL_CONTROLS)

    def makefile_syn_tcl(self, top_module):
        """Create a Diamond synthesis project by TCL"""
        syn_device = top_module.manifest_dict["syn_device"]
        syn_grade = top_module.manifest_dict["syn_grade"]
        syn_package = top_module.manifest_dict["syn_package"]
        create_tmp = self._tcl_controls["create"]
        target = syn_device + syn_grade + syn_package
        self._tcl_controls["create"] = create_tmp.format(target.upper())
        super(ToolDiamond, self).makefile_syn_tcl(top_module)

    def makefile_syn_files(self, fileset):
        """Write the files TCL section of the Makefile"""
        hdl = 'prj_src {0} \"{1}\"'
        self.writeln("define TCL_FILES")
        for file_aux in fileset:
            if isinstance(file_aux, LPFFile):
                self.writeln(hdl.format('add -exclude', file_aux.rel_path()))
                self.writeln(hdl.format('enable', file_aux.rel_path()))
            else:
                self.writeln(hdl.format('add', file_aux.rel_path()))
        self.writeln("endef")
        self.writeln("export TCL_FILES")

