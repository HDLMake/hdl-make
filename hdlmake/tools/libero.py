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

import subprocess
import sys
import os
import string

from hdlmake.action import ActionMakefile
from hdlmake.srcfile import VHDLFile, VerilogFile, SDCFile, PDCFile


LIBERO_STANDARD_LIBS = ['ieee', 'std']


class ToolLibero(ActionMakefile):

    """Class providing the interface for Microsemi Libero IDE synthesis"""

    TOOL_INFO = {
        'name': 'Libero',
        'id': 'libero',
        'windows_bin': 'libero',
        'linux_bin': 'libero',
        'project_ext': 'prjx'}

    SUPPORTED_FILES = [SDCFile, PDCFile]

    CLEAN_TARGETS = {'clean': ["$(PROJECT)", "run.tcl"],
                     'mrproper': ["*.pdb", "*.stp"]}

    TCL_CONTROLS = {'windows_interpreter': 'libero SCRIPT:',
                    'linux_interpreter': 'libero SCRIPT:',
                    'open': 'open_project -file {$(PROJECT)/$(PROJECT).prjx}',
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
        self.files = []
        self.filename = None
        self.syn_device = None
        self.syn_grade = None
        self.syn_package = None
        self.syn_top = None
        self.header = None
        self.tclname = 'temporal.tcl'

    def detect_version(self, path):
        """Get version for Microsemi Libero IDE synthesis"""
        return 'unknown'

    def generate_synthesis_project(
            self, update=False, tool_version='', top_mod=None, fileset=None):
        """Create a Microsemi Libero IDE synthesis project"""
        self.filename = top_mod.manifest_dict["syn_project"]
        self.syn_device = top_mod.manifest_dict["syn_device"]
        self.syn_grade = top_mod.manifest_dict["syn_grade"]
        self.syn_package = top_mod.manifest_dict["syn_package"]
        self.syn_top = top_mod.manifest_dict["syn_top"]

        if update is True:
            self.update_project()
        else:
            self.create_project()
        self.add_files(fileset)
        self.emit()
        self.execute()

    def emit(self, update=False):
        """Emit the TCL file that is required to generate the project"""
        file_aux = open(self.tclname, "w")
        file_aux.write(self.header + '\n')
        file_aux.write(self.__emit_files(update=update))
        file_aux.write('save_project\n')
        file_aux.write('close_project\n')
        file_aux.close()

    def execute(self):
        """Feed the TCL script to Microsemi Libero IDE command interpreter"""
        tmp = 'libero SCRIPT:{0}'
        cmd = tmp.format(self.tclname)
        process_aux = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
        # But do not wait till Libero finish, start displaying output
        # immediately ##
        while True:
            out = process_aux.stderr.read(1)
            if out == '' and process_aux.poll() is not None:
                break
            if out != '':
                sys.stdout.write(out)
                sys.stdout.flush()
        os.remove(self.tclname)

    def add_files(self, fileset):
        """Add files to the inner fileset"""
        for file_aux in fileset:
            self.files.append(file_aux)

    def create_project(self):
        """Create a new Microsemi Libero IDE project"""
        tmp = ('new_project -location {{./{0}}} -name {{{0}}} -hdl'
               ' {{VHDL}} -family {{ProASIC3}} -die {{{1}}} -package'
               ' {{{2}}} -speed {{{3}}} -die_voltage {{1.5}}')
        self.header = tmp.format(
            self.filename,
            self.syn_device.upper(),
            self.syn_package.upper(),
            self.syn_grade)

    def update_project(self):
        """Update an existing Microsemi Libero IDE project"""
        tmp = 'open_project -file {{{0}/{0}.prjx}}'
        self.header = tmp.format(self.filename)

    def __emit_files(self, update=False):
        """Emit the supported HDL files that need to be added to the project"""
        link_string = 'create_links {0} {{{1}}}'
        enable_string = ('organize_tool_files -tool {{{0}}} -file {{{1}}}'
                         ' -module {{{2}::work}} -input_type {{constraint}}')
        synthesis_constraints = []
        compilation_constraints = []
        ret = []
        # First stage: linking files
        for file_aux in self.files:
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
                '-module {' + self.syn_top + '::work} -input_type {constraint}'
            ret.append(line)
        # Third stage: Organizing / activating compilation constraints (the top
        # module needs to be present!)
        if compilation_constraints:
            line = 'organize_tool_files -tool {COMPILE} '
            for file_aux in compilation_constraints:
                line = line + '-file {' + file_aux.rel_path() + '} '
            line = line + \
                '-module {' + self.syn_top + '::work} -input_type {constraint}'
            ret.append(line)
        # Fourth stage: set root/top module
        line = 'set_root -module {' + self.syn_top + '::work}'
        ret.append(line)
        return ('\n'.join(ret)) + '\n'
