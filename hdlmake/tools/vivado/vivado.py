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

import subprocess
import sys
import os

import string
from string import Template
import fetch
import logging

from makefile_writer import MakefileWriter


VIVADO_STANDARD_LIBS = ['ieee', 'std']


class ToolControls(MakefileWriter):

    
    def detect_version(self, path):
        return 'unknown'

    
    def get_keys(self):
        tool_info = {
            'name': 'vivado',
            'id': 'vivado',
            'windows_bin': 'vivado',
            'linux_bin': 'vivado',
            'project_ext': 'xpr'
        }
        return tool_info

    def get_standard_libraries(self):
        return VIVADO_STANDARD_LIBS

    def generate_synthesis_makefile(self, top_mod, tool_path):
        makefile_tmplt = string.Template("""PROJECT := ${project_name}
VIVADO_CRAP := \
run.tcl

#target for performing local synthesis
local: syn_pre_cmd check_tool
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

check_tool:
\t\t${check_tool}

syn_post_cmd: local
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

.PHONY: mrproper clean syn_pre_cmd syn_post_cmd local check_tool

""")
        if top_mod.syn_pre_cmd:
            syn_pre_cmd = top_mod.syn_pre_cmd
        else:
            syn_pre_cmd = ''

        if top_mod.syn_post_cmd:
            syn_post_cmd = top_mod.syn_post_cmd
        else:
            syn_post_cmd = ''

        if top_mod.force_tool:
            ft = top_mod.force_tool
            check_tool = """python $(HDLMAKE_HDLMAKE_PATH)/hdlmake _conditioncheck --tool {tool} --reference {reference} --condition "{condition}"\\
|| (echo "{tool} version does not meet condition: {condition} {reference}" && false)
""".format(tool=ft[0],
                condition=ft[1],
                reference=ft[2])
        else:
            check_tool = ''

        makefile_text = makefile_tmplt.substitute(syn_top=top_mod.syn_top,
                                  project_name=top_mod.syn_project,
                                  planahead_path=tool_path,
                                  check_tool=check_tool,
                                  syn_pre_cmd=syn_pre_cmd,
                                  syn_post_cmd=syn_post_cmd,
                                  planahead_sh_path=os.path.join(tool_path, "planAhead"))
        self.write(makefile_text)
        for f in top_mod.incl_makefiles:
            if os.path.exists(f):
                self.write("include %s\n" % f)


    def generate_remote_synthesis_makefile(self, files, name, cwd, user, server):
        logging.info("Remote Vivado wrapper")


    def generate_synthesis_project(self, update=False, tool_version='', top_mod=None, fileset=None):
        self.properties = []
        self.files = []
        self.filename = top_mod.syn_project
        self.header = None
        self.tclname = 'temporal.tcl'
        if update is True:
            logging.info("Existing project detected: updating...")
            self.update_project()
        else:
            logging.info("No previous project: creating a new one...")
            self.create_project()
            self.add_initial_properties(top_mod.syn_device,
                                   top_mod.syn_grade,
                                   top_mod.syn_package,
                                   top_mod.syn_top)
        self.add_files(fileset)
        self.emit()
        self.execute()

        logging.info("Vivado project file generated.")


    def emit(self):
        f = open(self.tclname, "w")
        f.write(self.header+'\n')
        for p in self.properties:
            f.write(p.emit()+'\n')
        f.write(self.__emit_files())
        f.write('update_compile_order -fileset sources_1\n')
        f.write('update_compile_order -fileset sim_1\n')
        f.write('exit\n')
        f.close()

    def execute(self):
        tmp = 'vivado -mode tcl -source {0}'
        cmd = tmp.format(self.tclname)
        p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
        ## But do not wait till Vivado finish, start displaying output immediately ##
        while True:
            out = p.stderr.read(1)
            if out == '' and p.poll() != None:
                break
            if out != '':
                sys.stdout.write(out)
                sys.stdout.flush()
        os.remove(self.tclname)


    def add_files(self, fileset):
        for f in fileset:
            self.files.append(f)

    def add_property(self, new_property):
        self.properties.append(new_property)

    def add_initial_properties(self, 
                               syn_device,
                               syn_grade,
                               syn_package,
                               syn_top):
        PAPP = _VivadoProjectProperty
        self.add_property(PAPP(name='part', value=syn_device+syn_package+syn_grade, objects='current_project'))
        self.add_property(PAPP(name='target_language', value='VHDL', objects='current_project'))
        self.add_property(PAPP(name='ng.output_hdl_format', value='VHDL', objects='get_filesets sim_1'))
        # the bitgen b arg generates a raw configuration bitstream
        # self.add_property(PAPP(name='steps.bitgen.args.b', value='true', objects='get_runs impl_1'))
        self.add_property(PAPP(name='top', value=syn_top, objects='get_property srcset [current_run]'))


    def create_project(self):
        tmp = 'create_project {0} ./'
        self.header = tmp.format(self.filename)        

    def update_project(self):
        tmp = 'open_project ./{0}'
        self.header = tmp.format(self.filename+'.ppr')


    def __emit_properties(self):
        tmp = "set_property {0} {1} [{2}]"
        ret = []
        for p in self.properties:
            line = tmp.format(p.name, p.value, p.objects)
            ret.append(line)
        return ('\n'.join(ret))+'\n'


    def __emit_files(self):
        tmp = "add_files -norecurse {0}"
        ret = []
        from srcfile import VHDLFile, VerilogFile, SVFile, UCFFile, NGCFile, XMPFile, XCOFile
        for f in self.files:
            if isinstance(f, VHDLFile) or isinstance(f, VerilogFile) or isinstance(f, SVFile) or isinstance(f, UCFFile) or isinstance(f, NGCFile) or isinstance(f, XMPFile) or isinstance(f, XCOFile):
                line = tmp.format(f.rel_path())
            else:
                continue
            ret.append(line)
        return ('\n'.join(ret))+'\n'



class _VivadoProjectProperty:
    def __init__(self, name=None, value=None, objects=None):
        self.name = name
        self.value = value
        self.objects = objects

    def emit(self):
        tmp = "set_property {0} {1} [{2}]"
        line = tmp.format(self.name, self.value, self.objects)
        return(line)



