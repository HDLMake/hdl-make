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

from __future__ import print_function
import xml.dom.minidom
import xml.parsers.expat
import re
import os

import global_mod

import string
from string import Template
import fetch

from makefile_writer import MakefileWriter


XmlImpl = xml.dom.minidom.getDOMImplementation()

MODELSIM_STANDARD_LIBS = ['ieee', 'std']


class ToolControls(MakefileWriter):

    def detect_version(self, path):
        pass


    def get_keys(self):
        tool_info = {
            'name': 'Modelsim',
            'id': 'modelsim',
            'windows_bin': 'vsim',
            'linux_bin': 'vsim'
        }
        return tool_info

    def get_standard_libraries(self):
        return MODELSIM_STANDARD_LIBS

    def generate_simulation_makefile(self, fileset, top_module):
        from srcfile import VerilogFile, VHDLFile, SVFile
        make_preambule_p1 = """## variables #############################
PWD := $(shell pwd)

MODELSIM_INI_PATH := {0}

VCOM_FLAGS := -quiet -modelsimini modelsim.ini
VSIM_FLAGS :=
VLOG_FLAGS := -quiet -modelsimini modelsim.ini """ + self.__get_rid_of_vsim_incdirs(top_module.vlog_opt) + """
"""
        if global_mod.env["modelsim_path"]:
            make_preambule_p1 = make_preambule_p1.format(os.path.join(global_mod.env["modelsim_path"], ".."))
        else:
            make_preambule_p1 = make_preambule_p1.format(os.path.join("$(HDLMAKE_MODELSIM_PATH)", ".."))
        make_preambule_p2 = string.Template("""## rules #################################

local: sim_pre_cmd simulation sim_post_cmd

simulation: modelsim.ini $$(LIB_IND) $$(VERILOG_OBJ) $$(VHDL_OBJ)
$$(VERILOG_OBJ) : modelsim.ini
$$(VHDL_OBJ): $$(LIB_IND) modelsim.ini

sim_pre_cmd:
\t\t${sim_pre_cmd}

sim_post_cmd:
\t\t${sim_post_cmd}

modelsim.ini: ${modelsim_ini_path}
\t\tcp $$< . 2>&1
clean:
\t\trm -rf ./modelsim.ini $$(LIBS) transcript  *.vcd *.wlf
.PHONY: clean sim_pre_cmd sim_post_cmd simulation

""")
        #open the file and write the above preambule (part 1)
        self.write(make_preambule_p1)

        self.write("VERILOG_SRC := ")
        for vl in fileset.filter(VerilogFile):
            self.write(vl.rel_path() + " \\\n")
        self.write("\n")

        self.write("VERILOG_OBJ := ")
        for vl in fileset.filter(VerilogFile):
            #make a file compilation indicator (these .dat files are made even if
            #the compilation process fails) and add an ending according to file's
            #extension (.sv and .vhd files may have the same corename and this
            #causes a mess
            self.write(os.path.join(vl.library, vl.purename, "."+vl.purename+"_"+vl.extension()) + " \\\n")
        self.write('\n')

        libs = set(f.library for f in fileset)

        self.write("VHDL_SRC := ")
        for vhdl in fileset.filter(VHDLFile):
            self.write(vhdl.rel_path() + " \\\n")
        self.writeln()

        #list vhdl objects (_primary.dat files)
        self.write("VHDL_OBJ := ")
        for vhdl in fileset.filter(VHDLFile):
            #file compilation indicator (important: add _vhd ending)
            self.write(os.path.join(vhdl.library, vhdl.purename, "."+vhdl.purename+"_"+vhdl.extension()) + " \\\n")
        self.write('\n')

        self.write('LIBS := ')
        self.write(' '.join(libs))
        self.write('\n')
        #tell how to make libraries
        self.write('LIB_IND := ')
        self.write(' '.join([lib+"/."+lib for lib in libs]))
        self.write('\n')

        if top_module.sim_pre_cmd:
            sim_pre_cmd = top_module.sim_pre_cmd
        else:
            sim_pre_cmd = ''

        if top_module.sim_post_cmd:
            sim_post_cmd = top_module.sim_post_cmd
        else:
            sim_post_cmd = ''
        make_preambule_p2 = make_preambule_p2.substitute(sim_pre_cmd=sim_pre_cmd,
                                                         sim_post_cmd=sim_post_cmd,
                                                         modelsim_ini_path=os.path.join("$(MODELSIM_INI_PATH)", "modelsim.ini"))
        self.write(make_preambule_p2)

        for lib in libs:
            self.write(lib+"/."+lib+":\n")
            self.write(' '.join(["\t(vlib",  lib, "&&", "vmap", "-modelsimini modelsim.ini",
                       lib, "&&", "touch", lib+"/."+lib, ")"]))

            self.write(' '.join(["||", "rm -rf", lib, "\n"]))
            self.write('\n')

        #rules for all _primary.dat files for sv
        for vl in fileset.filter(VerilogFile):
            self.write("%s: %s" % (os.path.join(vl.library, vl.purename, ".%s_%s" % (vl.purename, vl.extension())),
                                   vl.rel_path())
                      )
            for dep_file in [dfile for dfile in vl.depends_on if dfile is not vl]:
                if dep_file in fileset: # the dep_file is compiled -> we depend on marker file
                    name = dep_file.purename
                    extension = dep_file.extension()
                    self.write(" \\\n" + os.path.join(dep_file.library, name, ".%s_%s" % (name, extension)))
                else: #the file is included -> we depend directly on the file
                    self.write(" \\\n" + dep_file.rel_path())

            self.writeln()

            ###
            # self.write("\t\tvlog -work "+vl.library)
            # self.write(" $(VLOG_FLAGS) ")
            # if isinstance(vl, SVFile):
            #     self.write(" -sv ")
            # incdir = "+incdir+"
            # incdir += '+'.join(vl.include_dirs)
            # incdir += " "
            # self.write(incdir)
            # self.writeln(vl.vlog_opt+" $<")
            ####
            compile_template = Template("\t\tvlog -work ${library} $$(VLOG_FLAGS) ${sv_option} +incdir+${include_dirs} ${vlog_opt} $$<")
            compile_line = compile_template.substitute(library=vl.library,
                                        sv_option = "-sv" if isinstance(vl, SVFile) else "",
                                        include_dirs='+'.join(vl.include_dirs),
                                        vlog_opt=vl.vlog_opt)
            self.writeln(compile_line)
            self.write("\t\t@mkdir -p $(dir $@)")
            self.writeln(" && touch $@ \n\n")
        self.write("\n")

        #list rules for all _primary.dat files for vhdl
        for vhdl in fileset.filter(VHDLFile):
            lib = vhdl.library
            purename = vhdl.purename
            #each .dat depends on corresponding .vhd file
            self.write("%s: %s" % (os.path.join(lib, purename, "."+purename+"_" + vhdl.extension()),
                                   vhdl.rel_path())
                       )
            for dep_file in vhdl.depends_on:
                if dep_file in fileset: # the dep_file is compiled -> we depend on marker file
                    name = dep_file.purename
                    extension = dep_file.extension()
                    self.write(" \\\n" + os.path.join(dep_file.library, name, ".%s_%s" % (name, extension)))
                else: #the file is included -> we depend directly on the file
                    self.write(" \\\n" + dep_file.rel_path())

            self.writeln()
            self.writeln(' '.join(["\t\tvcom $(VCOM_FLAGS)", vhdl.vcom_opt, "-work", lib, "$< "]))
            self.writeln("\t\t@mkdir -p $(dir $@) && touch $@\n")
            self.writeln()


    def __get_rid_of_vsim_incdirs(self, vlog_opt):
        if not vlog_opt:
            vlog_opt = ""
        vlogs = vlog_opt.split(' ')
        ret = []
        for v in vlogs:
            if not v.startswith("+incdir+"):
                ret.append(v)
        return ' '.join(ret)

