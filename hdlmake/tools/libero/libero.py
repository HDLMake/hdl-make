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
import logging

from hdlmake.makefile_writer import MakefileWriter


LIBERO_STANDARD_LIBS = ['ieee', 'std']


class ToolControls(MakefileWriter):


    def detect_version(self, path):
        return 'unknown'


    def get_keys(self):
        tool_info = {
            'name': 'Libero',
            'id': 'libero',
            'windows_bin': 'libero',
            'linux_bin': 'libero',
            'project_ext': 'prjx'  # older projects are prj
        }
        return tool_info

    def get_standard_libraries(self):
        return LIBERO_STANDARD_LIBS

    def generate_synthesis_makefile(self, top_mod, tool_path):
        makefile_tmplt = string.Template("""PROJECT := ${project_name}
LIBERO_CRAP := \
run.tcl

#target for performing local synthesis
local: syn_pre_cmd check_tool synthesis syn_post_cmd

synthesis:
\t\techo "open_project -file {$$(PROJECT)/$$(PROJECT).prjx}" > run.tcl
\t\techo "update_and_run_tool -name {GENERATEPROGRAMMINGDATA}" >> run.tcl
\t\techo "save_project" >> run.tcl
\t\techo "close_project" >> run.tcl
\t\t${libero_sh_path} SCRIPT:run.tcl
\t\tcp $$(PROJECT)/designer/impl1/${syn_top}.pdb ${syn_top}.pdb

check_tool:
\t\t${check_tool}

syn_post_cmd:
\t\t${syn_post_cmd}

syn_pre_cmd:
\t\t${syn_pre_cmd}

#target for cleaning all intermediate stuff
clean:
\t\trm -f $$(LIBERO_CRAP)
\t\trm -rf $$(PROJECT)

#target for cleaning final files
mrproper:
\t\trm -f *.pdb *.stp

.PHONY: mrproper clean syn_pre_cmd syn_post_cmd synthesis local check_tool

""")

        if top_mod.manifest_dict["syn_pre_cmd"]:
            syn_pre_cmd = top_mod.manifest_dict["syn_pre_cmd"]
        else:
            syn_pre_cmd = ''

        if top_mod.manifest_dict["syn_post_cmd"]:
            syn_post_cmd = top_mod.manifest_dict["syn_post_cmd"]
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

        makefile_text = makefile_tmplt.substitute(syn_top=top_mod.manifest_dict["syn_top"],
                                  project_name=top_mod.manifest_dict["syn_project"],
                                  libero_path=tool_path,
                                  check_tool=check_tool,
                                  syn_pre_cmd=syn_pre_cmd,
                                  syn_post_cmd=syn_post_cmd,
                                  libero_sh_path=os.path.join(tool_path, "libero"))
        self.write(makefile_text)
        for f in top_mod.incl_makefiles:
            if os.path.exists(f):
                self.write("include %s\n" % f)


    def generate_remote_synthesis_makefile(self, files, name, cwd, user, server):
        logging.info("Remote Libero wrapper")


    def generate_synthesis_project(self, update=False, tool_version='', top_mod=None, fileset=None):
        self.files = []
        self.filename = top_mod.manifest_dict["syn_project"]
        self.syn_device = top_mod.manifest_dict["syn_device"]
        self.syn_grade = top_mod.manifest_dict["syn_grade"]
        self.syn_package = top_mod.manifest_dict["syn_package"]
        self.syn_top = top_mod.manifest_dict["syn_top"]
        self.header = None
        self.tclname = 'temporal.tcl'

        if update is True:
            self.update_project()
        else:
            self.create_project()
        self.add_files(fileset)
        self.emit()
        self.execute()     


    def emit(self, update=False):
        f = open(self.tclname, "w")
        f.write(self.header+'\n')
        f.write(self.__emit_files(update=update))
        f.write('save_project\n')
        f.write('close_project\n')
        f.close()

    def execute(self):
        tmp = 'libero SCRIPT:{0}'
        cmd = tmp.format(self.tclname)
        p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
        ## But do not wait till Libero finish, start displaying output immediately ##
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

    def create_project(self):
        tmp = 'new_project -location {{./{0}}} -name {{{0}}} -hdl {{VHDL}} -family {{ProASIC3}} -die {{{1}}} -package {{{2}}} -speed {{{3}}} -die_voltage {{1.5}}'
        self.header = tmp.format(self.filename, self.syn_device.upper(), self.syn_package.upper(), self.syn_grade)

    def update_project(self):
        tmp = 'open_project -file {{{0}/{0}.prjx}}'
        self.header = tmp.format(self.filename)


    def __emit_files(self, update=False):
        link_string = 'create_links {0} {{{1}}}'
        enable_string = 'organize_tool_files -tool {{{0}}} -file {{{1}}} -module {{{2}::work}} -input_type {{constraint}}'
        synthesis_constraints = []
        compilation_constraints = []
        ret = []
        from hdlmake.srcfile import VHDLFile, VerilogFile, SDCFile, PDCFile
        # First stage: linking files
        for f in self.files:
            if isinstance(f, VHDLFile) or isinstance(f, VerilogFile):
                line = link_string.format('-hdl_source', f.rel_path())
            elif isinstance(f, SDCFile):
                line = link_string.format('-sdc', f.rel_path())
                synthesis_constraints.append(f)
                compilation_constraints.append(f)
            elif isinstance(f, PDCFile):
                line = link_string.format('-pdc', f.rel_path())
                compilation_constraints.append(f)
            else:
                continue
            ret.append(line)
        # Second stage: Organizing / activating synthesis constraints (the top module needs to be present!)
        if synthesis_constraints:
            line = 'organize_tool_files -tool {SYNTHESIZE} '
            for f in synthesis_constraints:
                line = line+'-file {'+f.rel_path()+'} '
            line = line+'-module {'+self.syn_top+'::work} -input_type {constraint}'
            ret.append(line)
        # Third stage: Organizing / activating compilation constraints (the top module needs to be present!)
        if compilation_constraints:
            line = 'organize_tool_files -tool {COMPILE} '
            for f in compilation_constraints:
                line = line+'-file {'+f.rel_path()+'} '
            line = line+'-module {'+self.syn_top+'::work} -input_type {constraint}'
            ret.append(line)
        # Fourth stage: set root/top module
        line = 'set_root -module {'+self.syn_top+'::work}'
        ret.append(line)
        return ('\n'.join(ret))+'\n'


    def supported_files(self, fileset):
        from hdlmake.srcfile import SDCFile, PDCFile, SourceFileSet
        sup_files = SourceFileSet()
        for f in fileset:
            if (isinstance(f, SDCFile)) or (isinstance(f, PDCFile)):
                sup_files.add(f)
            else:
                continue
        return sup_files

