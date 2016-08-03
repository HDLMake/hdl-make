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

"""Module providing support for Xilinx Vivado synthesis"""

import subprocess
import sys
import os
import string
import logging

from hdlmake.action import ActionMakefile
from hdlmake.srcfile import (VHDLFile, VerilogFile, SVFile, UCFFile,
                             NGCFile, XMPFile, XCOFile, BDFile, TCLFile)


VIVADO_STANDARD_LIBS = ['ieee', 'std']


class ToolVivado(ActionMakefile):

    """Class providing the interface for Xilinx Vivado synthesis"""

    TOOL_INFO = {
        'name': 'vivado',
        'id': 'vivado',
        'windows_bin': 'vivado',
        'linux_bin': 'vivado',
        'project_ext': 'xpr'
    }

    SUPPORTED_FILES = [UCFFile, NGCFile, XMPFile,
                       XCOFile, BDFile, TCLFile]

    def __init__(self):
        super(ToolVivado, self).__init__()
        self.properties = []
        self.files = []
        self.filename = None
        self.header = None
        self.tclname = 'temporal.tcl'

    def detect_version(self, path):
        """Get version from Xilinx Vivado binary program"""
        return 'unknown'

    def generate_synthesis_makefile(self, top_mod, tool_path):
        """Generate a synthesis Makefile for Xilinx Vivado"""
        makefile_tmplt = string.Template("""PROJECT := ${project_name}
VIVADO_CRAP := \
run.tcl

#target for performing local synthesis
local: syn_pre_cmd synthesis syn_post_cmd

synthesis:
\t\techo "open_project $$(PROJECT).xpr" > run.tcl
\t\techo "reset_run synth_1" >> run.tcl
\t\techo "reset_run impl_1" >> run.tcl
\t\techo "launch_runs synth_1" >> run.tcl
\t\techo "wait_on_run synth_1" >> run.tcl
\t\techo "launch_runs impl_1" >> run.tcl
\t\techo "wait_on_run impl_1" >> run.tcl
\t\techo "launch_runs impl_1 -to_step write_bitstream" >> run.tcl
\t\techo "wait_on_run impl_1" >> run.tcl
\t\techo "exit" >> run.tcl
\t\t${vivado_sh_path} -mode tcl -source run.tcl
\t\tcp $$(PROJECT).runs/impl_1/${syn_top}.bit ${syn_top}.bit

syn_post_cmd:
\t\t${syn_post_cmd}

syn_pre_cmd:
\t\t${syn_pre_cmd}

#target for cleaning all intermediate stuff
clean:
\t\trm -f $$(PLANAHEAD_CRAP)
\t\trm -rf .Xil $$(PROJECT).cache $$(PROJECT).data $$(PROJECT).runs $$(PROJECT).xpr

#target for cleaning final files
mrproper:
\t\trm -f *.bit

.PHONY: mrproper clean syn_pre_cmd syn_post_cmd synthesis local

""")

        if top_mod.manifest_dict["syn_pre_cmd"]:
            syn_pre_cmd = top_mod.manifest_dict["syn_pre_cmd"]
        else:
            syn_pre_cmd = ''

        if top_mod.manifest_dict["syn_post_cmd"]:
            syn_post_cmd = top_mod.manifest_dict["syn_post_cmd"]
        else:
            syn_post_cmd = ''

        makefile_text = makefile_tmplt.substitute(
            syn_top=top_mod.manifest_dict["syn_top"],
            project_name=top_mod.manifest_dict[
                "syn_project"],
            planahead_path=tool_path,
            syn_pre_cmd=syn_pre_cmd,
            syn_post_cmd=syn_post_cmd,
            vivado_sh_path=os.path.join(tool_path, "vivado"))
        self.write(makefile_text)
        for file_aux in top_mod.incl_makefiles:
            if os.path.exists(file_aux):
                self.write("include %s\n" % file_aux)

    def generate_synthesis_project(
            self, update=False, tool_version='', top_mod=None, fileset=None):
        """Generate a Xilinx Vivado synthesis project"""
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
        logging.info("Vivado project file generated.")

    def emit(self):
        """Emit the TCL file that will be feeded to the Vivado interpreter"""
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
        """Feed the TCL file to the Xilinx Vivado command line interpreter"""
        tmp = 'vivado -mode tcl -source {0}'
        cmd = tmp.format(self.tclname)
        process_aux = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
        # But do not wait till Vivado finish, start displaying output
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
        """Add a new propertiy to the Xilinx Vivado project"""
        self.properties.append(new_property)

    def add_initial_properties(self, syn_device, syn_grade,
                               syn_package, syn_top):
        """Add initial properties to the Xilinx Vivado project"""
        vivado_prop = _VivadoProjectProperty
        self.add_property(
            vivado_prop(
                name='part',
                value=syn_device +
                syn_package +
                syn_grade,
                objects='current_project'))
        # self.add_property(PAPP(name='board_part',
        # value='em.avnet.com:microzed_7010:part0:1.0',
        # objects='current_project'))
        self.add_property(
            vivado_prop(name='target_language',
                        value='VHDL',
                        objects='current_project'))

        # self.add_property(PAPP(name='ng.output_hdl_format',
        #                   value='VHDL', objects='get_filesets sim_1'))
        # the bitgen b arg generates a raw configuration bitstream
        # self.add_property(PAPP(name='steps.bitgen.args.b', value='true',
        # objects='get_runs impl_1'))
        self.add_property(
            vivado_prop(name='top',
                        value=syn_top,
                        objects='get_property srcset [current_run]'))

    def create_project(self):
        """Create an empty Xilinx Vivado project"""
        tmp = 'create_project {0} ./'
        self.header = tmp.format(self.filename)

    def update_project(self):
        """Update an existing Xilinx Vivado project"""
        tmp = 'open_project ./{0}'
        self.header = tmp.format(self.filename + '.xpr')

    def __emit_properties(self):
        """Emit the properties to be added to the project"""
        tmp = "set_property {0} {1} [{2}]"
        ret = []
        for prop in self.properties:
            line = tmp.format(prop.name, prop.value, prop.objects)
            ret.append(line)
        return ('\n'.join(ret)) + '\n'

    def __emit_files(self):
        """Emit the design HDL files that must be added to the project"""
        tmp = "add_files -norecurse {0}"
        tcl = "source {0}"
        ret = []
        for file_aux in self.files:
            if (isinstance(file_aux, VHDLFile) or
                isinstance(file_aux, VerilogFile) or
                isinstance(file_aux, SVFile) or
                isinstance(file_aux, UCFFile) or
                isinstance(file_aux, NGCFile) or
                isinstance(file_aux, XMPFile) or
                isinstance(file_aux, XCOFile) or
                    isinstance(file_aux, BDFile)):
                line = tmp.format(file_aux.rel_path())
            elif isinstance(file_aux, TCLFile):
                line = tcl.format(file_aux.rel_path())
            else:
                continue
            ret.append(line)
        return ('\n'.join(ret)) + '\n'


class _VivadoProjectProperty(object):

    """Class providing an storage for Xilinx Vivado properties"""

    def __init__(self, name=None, value=None, objects=None):
        self.name = name
        self.value = value
        self.objects = objects

    def emit(self):
        """Emit the Xilinx Vivado property the class instance contains"""
        tmp = "set_property {0} {1} [{2}]"
        line = tmp.format(self.name, self.value, self.objects)
        return line
