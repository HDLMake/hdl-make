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

import os
import sys

import string
from string import Template
import fetch
import logging

from makefile_writer import MakefileWriter


QUARTUS_STANDARD_LIBS = ['altera', 'altera_mf', 'lpm', 'ieee', 'std']


class ToolControls(MakefileWriter):


    def detect_version(self, path):
        return 'unknown'


    def get_keys(self):
        tool_info = {
            'name': 'Quartus',
            'id': 'quartus',
            'windows_bin': 'quartus',
            'linux_bin': 'quartus',
            'project_ext': 'qsf'
        }
        return tool_info

    def get_standard_libraries(self):
        return QUARTUS_STANDARD_LIBS

    def generate_synthesis_makefile(self, top_mod, tool_path):
        makefile_tmplt = string.Template("""PROJECT := ${project_name}
QUARTUS_CRAP := \
$$(PROJECT).asm.rpt \
$$(PROJECT).done \
$$(PROJECT).fit.rpt \
$$(PROJECT).fit.smsg \
$$(PROJECT).fit.summary \
$$(PROJECT).flow.rpt \
$$(PROJECT).jdi \
$$(PROJECT).map.rpt \
$$(PROJECT).map.summary \
$$(PROJECT).pin \
$$(PROJECT).qws \
$$(PROJECT).sta.rpt \
$$(PROJECT).sta.summary \
run.tcl

#target for performing local synthesis
local: syn_pre_cmd check_tool synthesis syn_post_cmd

synthesis:
\t\techo "load_package flow" > run.tcl
\t\techo "project_open $$(PROJECT)" >> run.tcl
\t\techo "execute_flow -compile" >> run.tcl
\t\t${quartus_sh_path} -t run.tcl

check_tool:
\t\t${check_tool}

syn_post_cmd:
\t\t${syn_post_cmd}

syn_pre_cmd:
\t\t${syn_pre_cmd}

#target for cleaing all intermediate stuff
clean:
\t\trm -f $$(QUARTUS_CRAP)
\t\trm -rf db incremental_db

#target for cleaning final files
mrproper:
\t\trm -f *.sof *.pof *.jam *.jbc *.ekp *.jic

.PHONY: mrproper clean syn_pre_cmd syn_post_cmd synthesis local check_tool

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
                                  quartus_path=tool_path,
                                  check_tool=check_tool,
                                  syn_pre_cmd=syn_pre_cmd,
                                  syn_post_cmd=syn_post_cmd,
                                  quartus_sh_path=os.path.join(tool_path, "quartus_sh"))
        self.write(makefile_text)
        for f in top_mod.incl_makefiles:
            if os.path.exists(f):
                self.write("include %s\n" % f)


    def generate_remote_synthesis_makefile(self, files, name, cwd, user, server):
        logging.info("Remote Quartus wrapper")
        


    def generate_synthesis_project(self, update=False, tool_version='', top_mod=None, fileset=None):
        self.properties = []
        self.files = []
        self.filename = top_mod.syn_project
        self.preflow = top_mod.quartus_preflow
        self.postmodule = top_mod.quartus_postmodule
        self.postflow = top_mod.quartus_postflow

        if update is True:
            self.read()
        else:
            self.add_initial_properties(top_mod.syn_device,
                                       top_mod.syn_grade,
                                       top_mod.syn_package,
                                       top_mod.syn_top)
        self.add_files(fileset)
        self.emit()


    def emit(self):
        f = open(self.filename+'.qsf', "w")
        for p in self.properties:
            f.write(p.emit()+'\n')
        f.write(self.__emit_files())
        f.write(self.__emit_scripts())
        f.close()
        f = open(self.filename+'.qpf', "w")
        f.write("PROJECT_REVISION = \"" + self.filename + "\"\n")
        f.close()

    def __emit_scripts(self):
        tmp = 'set_global_assignment -name {0} "quartus_sh:{1}"'
        pre = mod = post = ""
        if self.preflow:
            pre = tmp.format("PRE_FLOW_SCRIPT_FILE", self.preflow.rel_path())
        if self.postmodule:
            mod = tmp.format("POST_MODULE_SCRIPT_FILE", self.postmodule.rel_path())
        if self.postflow:
            post = tmp.format("POST_FLOW_SCRIPT_FILE", self.postflow.rel_path())
        return pre+'\n'+mod+'\n'+post+'\n'

    def __emit_files(self):
        from srcfile import VHDLFile, VerilogFile, SignalTapFile, SDCFile, QIPFile, DPFFile
        tmp = "set_global_assignment -name {0} {1}"
        ret = []
        for f in self.files:
            if isinstance(f, VHDLFile):
                line = tmp.format("VHDL_FILE", f.rel_path())
            elif isinstance(f, VerilogFile):
                line = tmp.format("VERILOG_FILE", f.rel_path())
            elif isinstance(f, SignalTapFile):
                line = tmp.format("SIGNALTAP_FILE", f.rel_path())
            elif isinstance(f, SDCFile):
                line = tmp.format("SDC_FILE", f.rel_path())
            elif isinstance(f, QIPFile):
                line = tmp.format("QIP_FILE", f.rel_path())
            elif isinstance(f, DPFFile):
                line = tmp.format("MISC_FILE", f.rel_path())
            else:
                continue
            ret.append(line)
        return ('\n'.join(ret))+'\n'

    def add_property(self, val):
        #don't save files (they are unneeded)
        if val.name_type is not None and "_FILE" in val.name_type:
            return
        self.properties.append(val)

    def add_files(self, fileset):
        for f in fileset:
            self.files.append(f)

    def read(self):
        def __gather_string(words, first_index):
            i = first_index
            ret = []
            if words[i][0] != '"':
                return (words[i], 1)
            else:
                while True:
                    ret.append(words[i])
                    if words[i][len(words[i])-1] == '"':
                        return (' '.join(ret), len(ret))
                    i = i + 1

        f = open(self.filename+'.qsf', "r")
        lines = [l.strip() for l in f.readlines()]
        lines = [l for l in lines if l != "" and l[0] != '#']
        QPP = _QuartusProjectProperty
        for line in lines:
            words = line.split()
            command = QPP.t[words[0]]
            what = name = name_type = from_ = to = section_id = None
            i = 1
            while True:
                if i >= len(words):
                    break

                if words[i] == "-name":
                    name_type = words[i+1]
                    name, add = __gather_string(words, i+2)
                    i = i+2+add
                    continue
                elif words[i] == "-section_id":
                    section_id, add = __gather_string(words, i+1)
                    i = i+1+add
                    continue
                elif words[i] == "-to":
                    to, add = __gather_string(words, i+1)
                    i = i+1+add
                    continue
                elif words[i] == "-from":
                    from_, add = __gather_string(words, i+1)
                    i = i+2
                    continue
                else:
                    what = words[i]
                    i = i+1
                    continue
            prop = QPP(command=command,
                       what=what, name=name,
                       name_type=name_type,
                       from_=from_,
                       to=to,
                       section_id=section_id)

            self.add_property(prop)
        f.close()

    def add_initial_properties(self, syn_device, syn_grade, syn_package, syn_top):
        import re
        family_names = {
            "^EP2AGX.*$": "Arria II GX",
            "^EP3C.*$": "Cyclone III",
            "^5S.*$": "Stratix V",
        }

        for key in family_names:
            if re.match(key, syn_device.upper()):
                family = family_names[key]

        devstring = (syn_device + syn_package + syn_grade).upper()
        QPP = _QuartusProjectProperty
        self.add_property(QPP(QPP.SET_GLOBAL_ASSIGNMENT, name_type='FAMILY', name='"'+family+'"'))
        self.add_property(QPP(QPP.SET_GLOBAL_ASSIGNMENT, name_type='DEVICE', name=devstring))
        self.add_property(QPP(QPP.SET_GLOBAL_ASSIGNMENT, name_type='TOP_LEVEL_ENTITY', name=syn_top))




class _QuartusProjectProperty:
    SET_GLOBAL_INSTANCE, SET_INSTANCE_ASSIGNMENT, SET_LOCATION_ASSIGNMENT, SET_GLOBAL_ASSIGNMENT = range(4)
    t = {"set_global_instance": SET_GLOBAL_INSTANCE,
         "set_instance_assignment": SET_INSTANCE_ASSIGNMENT,
         "set_location_assignment": SET_LOCATION_ASSIGNMENT,
         "set_global_assignment": SET_GLOBAL_ASSIGNMENT}

    def __init__(self, command, what=None, name=None, name_type=None, from_=None, to=None, section_id=None):
        self.command = command
        self.what = what
        self.name = name
        self.name_type = name_type
        self.from_ = from_
        self.to = to
        self.section_id = section_id

    def emit(self):
        words = []
        words.append(dict([(b, a) for a, b in self.t.items()])[self.command])

        if self.what is not None:
            words.append(self.what)
        if self.name is not None:
            words.append("-name")
            words.append(self.name_type)
            words.append(self.name)
        if self.from_ is not None:
            words.append("-from")
            words.append(self.from_)
        if self.to is not None:
            words.append("-to")
            words.append(self.to)
        if self.section_id is not None:
            words.append("-section_id")
            words.append(self.section_id)
        return ' '.join(words)



