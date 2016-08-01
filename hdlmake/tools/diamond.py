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
import logging
import string

from hdlmake.makefile_writer import MakefileWriter

DIAMOND_STANDARD_LIBS = ['ieee', 'std']


class ToolDiamond(MakefileWriter):

    def __init__(self):
        super(ToolDiamond, self).__init__()

    def detect_version(self, path):
        return 'unknown'

    def get_keys(self):
        tool_info = {
            'name': 'Diamond',
            'id': 'diamond',
            'windows_bin': 'pnmainc',
            'linux_bin': 'diamondc',
            'project_ext': 'ldf'
        }
        return tool_info

    def get_standard_libraries(self):
        return DIAMOND_STANDARD_LIBS

    def generate_synthesis_makefile(self, top_mod, tool_path):
        makefile_tmplt = string.Template("""PROJECT := ${project_name}
DIAMOND_CRAP := \
$$(PROJECT)1.sty \
run.tcl

#target for performing local synthesis
local: syn_pre_cmd synthesis syn_post_cmd

synthesis:
\t\techo "prj_project open \"$$(PROJECT).ldf\"" > run.tcl
\t\techo "prj_run PAR -impl $$(PROJECT)" >> run.tcl
\t\techo "prj_run Export -impl $$(PROJECT) -task Bitgen" >> run.tcl
\t\techo "prj_project close" >> run.tcl
\t\t${diamondc_path} run.tcl
\t\tcp $$(PROJECT)/$$(PROJECT)_$$(PROJECT).jed $$(PROJECT).jed

syn_post_cmd:
\t\t${syn_post_cmd}

syn_pre_cmd:
\t\t${syn_pre_cmd}

#target for cleaing all intermediate stuff
clean:
\t\trm -f $$(DIAMOND_CRAP)
\t\trm -rf $$(PROJECT)

#target for cleaning final files
mrproper:
\t\trm -f *.jed

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

        if sys.platform == 'cygwin':
            bin_name = 'pnmainc'
        else:
            bin_name = 'diamondc'
        makefile_text = makefile_tmplt.substitute(
            syn_top=top_mod.manifest_dict["syn_top"],
            project_name=top_mod.manifest_dict[
                "syn_project"],
            diamond_path=tool_path,
            syn_pre_cmd=syn_pre_cmd,
            syn_post_cmd=syn_post_cmd,
            diamondc_path=os.path.join(tool_path, bin_name))
        self.write(makefile_text)
        for f in top_mod.incl_makefiles:
            if os.path.exists(f):
                self.write("include %s\n" % f)

    def generate_remote_synthesis_makefile(
            self, files, name, cwd, user, server):
        logging.info("Remote Diamond wrapper")

    def generate_synthesis_project(
            self, update=False, tool_version='', top_mod=None, fileset=None):
        self.files = []
        self.filename = top_mod.manifest_dict["syn_project"]
        self.header = None
        self.tclname = 'temporal.tcl'
        if update is True:
            self.update_project()
        else:
            self.create_project(top_mod.manifest_dict["syn_device"],
                                top_mod.manifest_dict["syn_grade"],
                                top_mod.manifest_dict["syn_package"],
                                top_mod.manifest_dict["syn_top"])
        self.add_files(fileset)
        self.emit(update=update)
        self.execute()

    def emit(self, update=False):
        f = open(self.tclname, "w")
        f.write(self.header + '\n')
        f.write(self.__emit_files(update=update))
        f.write('prj_project save\n')
        f.write('prj_project close\n')
        f.close()

    def execute(self):
        # The binary name for Diamond is different in Linux and Windows
        if sys.platform == 'cygwin':
            tmp = 'pnmainc {0}'
        else:
            tmp = 'diamondc {0}'
        cmd = tmp.format(self.tclname)
        p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
        # But do not wait till diamond finish, start displaying output
        # immediately ##
        while True:
            out = p.stderr.read(1)
            if out == '' and p.poll() is not None:
                break
            if out != '':
                sys.stdout.write(out)
                sys.stdout.flush()
        os.remove(self.tclname)

    def add_files(self, fileset):
        for f in fileset:
            self.files.append(f)

    def create_project(self,
                       syn_device,
                       syn_grade,
                       syn_package,
                       syn_top):
        tmp = 'prj_project new -name {0} -impl {0} -dev {1} -synthesis \"synplify\"'
        target = syn_device + syn_grade + syn_package
        self.header = tmp.format(self.filename, target.upper())

    def update_project(self):
        tmp = 'prj_project open \"{0}\"'
        self.header = tmp.format(self.filename + '.ldf')

    def supported_files(self, fileset):
        from hdlmake.srcfile import EDFFile, LPFFile, SourceFileSet
        sup_files = SourceFileSet()
        for f in fileset:
            if (isinstance(f, EDFFile)) or (isinstance(f, LPFFile)):
                sup_files.add(f)
            else:
                continue
        return sup_files

    def __emit_files(self, update=False):
        tmp = 'prj_src {0} \"{1}\"'
        ret = []
        from hdlmake.srcfile import VHDLFile, VerilogFile, SVFile, EDFFile, LPFFile
        for f in self.files:
            line = ''
            if isinstance(f, VHDLFile) or isinstance(f, VerilogFile) or isinstance(f, SVFile) or isinstance(f, EDFFile):
                if update:
                    line = line + '\n' + tmp.format('remove', f.rel_path())
                line = line + '\n' + tmp.format('add', f.rel_path())
            elif isinstance(f, LPFFile):
                if update:
                    line = line + '\n' + \
                        tmp.format('enable', self.filename + '.lpf')
                    line = line + '\n' + tmp.format('remove', f.rel_path())
                line = line + '\n' + tmp.format('add -exclude', f.rel_path())
                line = line + '\n' + tmp.format('enable', f.rel_path())
            else:
                continue
            ret.append(line)
        return ('\n'.join(ret)) + '\n'
