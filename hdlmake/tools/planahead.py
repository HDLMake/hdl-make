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

"""Module providing support for Xilinx PlanAhead synthesis"""

import subprocess
import sys
import os
import string
import logging

from hdlmake.action import ActionMakefile
from hdlmake.srcfile import (VHDLFile, VerilogFile, SVFile,
                             UCFFile, NGCFile, XMPFile, XCOFile)


PLANAHEAD_STANDARD_LIBS = ['ieee', 'std']


class ToolPlanAhead(ActionMakefile):

    """Class providing the interface for Xilinx PlanAhead synthesis"""

    TOOL_INFO = {
        'name': 'PlanAhead',
        'id': 'planahead',
        'windows_bin': 'planAhead',
        'linux_bin': 'planAhead',
        'project_ext': 'ppr'}

    SUPPORTED_FILES = [UCFFile, NGCFile, XMPFile, XCOFile]

    CLEAN_TARGETS = {'clean': ["planAhead_*", "planAhead.*", "run.tcl",
                               ".Xil", "$(PROJECT).cache", "$(PROJECT).data",
                               " $(PROJECT).runs", "$(PROJECT).ppr"],
                     'mrproper': ["*.bit", "*.bin"]}

    TCL_CONTROLS = {'windows_interpreter': 'planAhead -mode tcl -source ',
                    'linux_interpreter': 'planAhead -mode tcl -source ',
                    'open': 'open_project $(PROJECT).ppr',
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
                    'bitstream': 'launch_runs impl_1 -to_step Bitgen\n'
                                 'wait_on_run impl_1',
                    'install_source': '$(PROJECT).runs/impl_1/$(SYN_TOP).bit'}

    def __init__(self):
        super(ToolPlanAhead, self).__init__()
        self.properties = []
        self.files = []
        self.filename = None
        self.header = None
        self.tclname = 'temporal.tcl'

    def detect_version(self, path):
        """Get the Xilinx PlanAhead program version"""
        return 'unknown'

    def generate_synthesis_project(
            self, update=False, tool_version='', top_mod=None, fileset=None):
        """Create a Xilinx PlanAhead project"""
        self.filename = top_mod.manifest_dict["syn_project"]
        if update is True:
            logging.info("Existing project detected: updating...")
            self.update_project()
        else:
            logging.info("No previous project: creating a new one...")
            self.create_project()
            self.add_initial_properties(top_mod.manifest_dict["syn_device"],
                                        top_mod.manifest_dict["syn_grade"],
                                        top_mod.manifest_dict["syn_package"],
                                        top_mod.manifest_dict["syn_top"])
        self.add_files(fileset)
        self.emit()
        self.execute()
        logging.info("PlanAhead project file generated.")

    def emit(self):
        """Emit the TCL file that will be used to generate the project"""
        file_aux = open(self.tclname, "w")
        file_aux.write(self.header + '\n')
        for prop in self.properties:
            file_aux.write(prop.emit() + '\n')
        file_aux.write(self.__emit_files())
        file_aux.write('update_compile_order -fileset sources_1\n')
        file_aux.write('update_compile_order -fileset sim_1\n')
        file_aux.write('exit\n')
        file_aux.close()

    def execute(self):
        """Source the TCL file to the Xilinx PlanAhead interpreter"""
        tmp = 'planAhead -mode tcl -source {0}'
        cmd = tmp.format(self.tclname)
        process_aux = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
        # But do not wait till planahead finish, start displaying output
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

    def add_property(self, new_property):
        """Add a new Xilinx PlanAhead property to the defined set"""
        self.properties.append(new_property)

    def add_initial_properties(self,
                               syn_device,
                               syn_grade,
                               syn_package,
                               syn_top):
        """Add the initial properties to the Xilinx PlanAhead project"""
        prop = _PlanAheadProjectProperty
        self.add_property(
            prop(
                name='part',
                value=syn_device +
                syn_package +
                syn_grade,
                objects='current_project'))
        self.add_property(
            prop(name='target_language',
                         value='VHDL',
                         objects='current_project'))
        self.add_property(
            prop(
                name='ng.output_hdl_format',
                value='VHDL',
                objects='get_filesets sim_1'))
        # the bitgen b arg generates a raw configuration bitstream
        # self.add_property(PAPP(name='steps.bitgen.args.b', value='true',
        # objects='get_runs impl_1'))
        self.add_property(
            prop(name='top',
                         value=syn_top,
                         objects='get_property srcset [current_run]'))

    def create_project(self):
        """Create an empty Xilinx PlanAhead project"""
        tmp = 'create_project {0} ./'
        self.header = tmp.format(self.filename)

    def update_project(self):
        """Update an existing Xilinx PlanAhead project"""
        tmp = 'open_project ./{0}'
        self.header = tmp.format(self.filename + '.ppr')

    def __emit_properties(self):
        """Add to the project the different properties that have been defined"""
        tmp = "set_property {0} {1} [{2}]"
        ret = []
        for prop in self.properties:
            line = tmp.format(prop.name, prop.value, prop.objects)
            ret.append(line)
        return ('\n'.join(ret)) + '\n'

    def __emit_files(self):
        """Add to the project the different files defined in the design"""
        tmp = "add_files -norecurse {0}"
        ret = []
        for file_aux in self.files:
            if (isinstance(file_aux, VHDLFile) or
                isinstance(file_aux, VerilogFile) or
                isinstance(file_aux, SVFile) or
                isinstance(file_aux, UCFFile) or
                isinstance(file_aux, NGCFile) or
                isinstance(file_aux, XMPFile) or
                    isinstance(file_aux, XCOFile)):
                line = tmp.format(file_aux.rel_path())
            else:
                continue
            ret.append(line)
        return ('\n'.join(ret)) + '\n'


class _PlanAheadProjectProperty(object):

    """Class that serves as a convenient storage for PlanAhead properties"""

    def __init__(self, name=None, value=None, objects=None):
        self.name = name
        self.value = value
        self.objects = objects

    def emit(self):
        """Emit the property defined by the class inner parameters"""
        tmp = "set_property {0} {1} [{2}]"
        line = tmp.format(self.name, self.value, self.objects)
        return line
