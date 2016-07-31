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
import platform
import string

from hdlmake.makefile_writer import MakefileWriter


class VsimMakefileWriter(MakefileWriter):
    """A Makefile writer for simulation suitable for vsim based simulators.

    Currently used by:
      - Modelsim
      - Riviera
    """
    def __init__(self):

        # additional global flags to pass to every invocation of these commands
        self.vcom_flags = ["-quiet", ]
        self.vsim_flags = []
        self.vlog_flags = ["-quiet", ]
        self.vmap_flags = []

        # These are variables that will be set in the makefile
        # The key is the variable name, and the value is the variable value
        self.custom_variables = {}

        # Additional sim dependencies (e.g. modelsim.ini)
        self.additional_deps = []

        # Additional things removed during a clean e.g. simulator temp files
        self.additional_clean = []

        # These are files copied into your working directory by a make rule
        # The key is the filename, the value is the file source path
        self.copy_rules = {}
        super(VsimMakefileWriter, self).__init__()

    def generate_simulation_makefile(self, fileset, top_module):
        """Write a properly formatted Makefile for the simulator.

        The Makefile format is shared, but flags, dependencies, clean rules,
        etc are defined by the specific tool.
        """
        from hdlmake.srcfile import VerilogFile, VHDLFile, SVFile
        
        if platform.system() == 'Windows': 
            del_command = "rm -rf"
            mkdir_command = "mkdir"
            slash_char = "\\"
        else: 
            del_command = "rm -rf"
            mkdir_command = "mkdir -p"
            slash_char = "/"
        
        self.vlog_flags.append(self.__get_rid_of_vsim_incdirs(top_module.manifest_dict["vlog_opt"]))
        self.vcom_flags.append(top_module.manifest_dict["vcom_opt"])
        self.vmap_flags.append(top_module.manifest_dict["vmap_opt"])
        self.vsim_flags.append(top_module.manifest_dict["vsim_opt"])

        tmp = """## variables #############################
PWD := $(shell pwd)
"""
        self.write(tmp)
        self.writeln()

        for var, value in self.custom_variables.iteritems():
            self.writeln("%s := %s" % (var, value))
        self.writeln()

        self.writeln("VCOM_FLAGS := %s" % (' '.join(self.vcom_flags)))
        self.writeln("VSIM_FLAGS := %s" % (' '.join(self.vsim_flags)))
        self.writeln("VLOG_FLAGS := %s" % (' '.join(self.vlog_flags)))
        self.writeln("VMAP_FLAGS := %s" % (' '.join(self.vmap_flags)))
        #self.writeln("INCLUDE_DIRS := +incdir+%s" % ('+'.join(top_module.include_dirs)))

        self.write("VERILOG_SRC := ")
        for vl in fileset.filter(VerilogFile):
            self.write(vl.rel_path() + " \\\n")
        self.write("\n")

        self.write("VERILOG_OBJ := ")
        for vl in fileset.filter(VerilogFile):
            # make a file compilation indicator (these .dat files are made even if
            # the compilation process fails) and add an ending according to file's
            # extension (.sv and .vhd files may have the same corename and this
            # causes a mess
            self.write(os.path.join(vl.library, vl.purename, "." + vl.purename + "_" + vl.extension()) + " \\\n")
        self.write('\n')

        libs = set(f.library for f in fileset)

        self.write("VHDL_SRC := ")
        for vhdl in fileset.filter(VHDLFile):
            self.write(vhdl.rel_path() + " \\\n")
        self.writeln()

        # list vhdl objects (_primary.dat files)
        self.write("VHDL_OBJ := ")
        for vhdl in fileset.filter(VHDLFile):
            # file compilation indicator (important: add _vhd ending)
            self.write(os.path.join(vhdl.library, vhdl.purename, "." + vhdl.purename + "_" + vhdl.extension()) + " \\\n")
        self.write('\n')

        self.write('LIBS := ')
        self.write(' '.join(libs))
        self.write('\n')
        # tell how to make libraries
        self.write('LIB_IND := ')
        self.write(' '.join([lib + slash_char + "." + lib for lib in libs]))
        self.write('\n')

        self.writeln("## rules #################################")
        self.writeln()
        self.writeln("local: sim_pre_cmd simulation sim_post_cmd")
        self.writeln()
        self.writeln("simulation: %s $(LIB_IND) $(VERILOG_OBJ) $(VHDL_OBJ)" % (' '.join(self.additional_deps)),)
        self.writeln("$(VERILOG_OBJ) : " + ' '.join(self.additional_deps))
        self.writeln("$(VHDL_OBJ): $(LIB_IND) " + ' '.join(self.additional_deps))
        self.writeln()

        simcommands = string.Template("""sim_pre_cmd:
\t\t${sim_pre_cmd}

sim_post_cmd:
\t\t${sim_post_cmd}
""")

        if top_module.manifest_dict["sim_pre_cmd"]:
            sim_pre_cmd = top_module.manifest_dict["sim_pre_cmd"]
        else:
            sim_pre_cmd = ''

        if top_module.manifest_dict["sim_post_cmd"]:
            sim_post_cmd = top_module.manifest_dict["sim_post_cmd"]
        else:
            sim_post_cmd = ''


        simcommands = simcommands.substitute(sim_pre_cmd=sim_pre_cmd,
                                                                         sim_post_cmd=sim_post_cmd)
        self.write(simcommands)
        self.writeln()

        for filename, filesource in self.copy_rules.iteritems():
            self.write(self.__create_copy_rule(filename, filesource))

        self.writeln("clean:")
        tmp = "\t\t" + del_command + " $(LIBS) " + ' '.join(self.additional_clean)
        self.writeln(tmp)

        self.writeln(".PHONY: clean sim_pre_cmd sim_post_cmd simulation")
        self.writeln()

        for lib in libs:
            self.write(lib + slash_char + "." + lib + ":\n")
            vmap_command = "vmap $(VMAP_FLAGS)"
            self.write(' '.join(["\t(vlib", lib, "&&", vmap_command,
                                         lib, "&&", "touch", lib + slash_char + "." + lib, ")"]))
            self.write(' '.join(["||", del_command, lib, "\n"]))
            self.write('\n\n')

        # rules for all _primary.dat files for sv
        for vl in fileset.filter(VerilogFile):
            self.write("%s: %s" % (os.path.join(vl.library, vl.purename, ".%s_%s" % (vl.purename, vl.extension())),
                                          vl.rel_path())
                         )
            # list dependencies, do not include the target file
            for dep_file in [dfile for dfile in vl.depends_on if dfile is not vl]:
                if dep_file in fileset: # the dep_file is compiled -> we depend on marker file
                    name = dep_file.purename
                    extension = dep_file.extension()
                    self.write(" \\\n" + os.path.join(dep_file.library, name, ".%s_%s" % (name, extension)))
                else: #the file is included -> we depend directly on the file
                    self.write(" \\\n" + dep_file.rel_path())

            self.writeln()

            # ##
            # self.write("\t\tvlog -work "+vl.library)
            # self.write(" $(VLOG_FLAGS) ")
            # if isinstance(vl, SVFile):
            #      self.write(" -sv ")
            # incdir = "+incdir+"
            # incdir += '+'.join(vl.include_dirs)
            # incdir += " "
            # self.write(incdir)
            # self.writeln(vl.vlog_opt+" $<")
            ####
            compile_template = string.Template("\t\tvlog -work ${library} $$(VLOG_FLAGS) ${sv_option} $${INCLUDE_DIRS} $$<")
            compile_line = compile_template.substitute(library=vl.library,
                                                 sv_option="-sv" if isinstance(vl, SVFile) else "")
            self.writeln(compile_line)
            self.write("\t\t@" + mkdir_command + " $(dir $@)")
            self.writeln(" && touch $@ \n\n")
            self.write("\n")

        # list rules for all _primary.dat files for vhdl
        for vhdl in fileset.filter(VHDLFile):
            lib = vhdl.library
            purename = vhdl.purename
            # each .dat depends on corresponding .vhd file
            self.write("%s: %s" % (os.path.join(lib, purename, "." + purename + "_" + vhdl.extension()),
                                          vhdl.rel_path())
                          )
            # list dependencies, do not include the target file
            for dep_file in [dfile for dfile in vhdl.depends_on if dfile is not vhdl]:
                if dep_file in fileset: # the dep_file is compiled -> we depend on marker file
                    name = dep_file.purename
                    extension = dep_file.extension()
                    self.write(" \\\n" + os.path.join(dep_file.library, name, ".%s_%s" % (name, extension)))
                else: #the file is included -> we depend directly on the file
                    self.write(" \\\n" + dep_file.rel_path())

            self.writeln()
            self.writeln(' '.join(["\t\tvcom $(VCOM_FLAGS)", vhdl.vcom_opt, "-work", lib, "$< "]))
            self.writeln("\t\t@" + mkdir_command + " $(dir $@) && touch $@ \n")
            self.writeln()

    def __create_copy_rule(self, name, src):
        """Get a Makefile rule named name, which depends on src, copying it to
        the local directory."""
        if platform.system() == 'Windows': copy_command = "copy"
        else: copy_command = "cp"
        rule = """%s: %s
\t\t%s $< . 2>&1
""" % (name, src, copy_command)
        return rule

    def __get_rid_of_vsim_incdirs(self, vlog_opt=""):
        if not vlog_opt:
            vlog_opt = ""
        vlogs = vlog_opt.split(' ')
        ret = []
        for v in vlogs:
            if not v.startswith("+incdir+"):
                ret.append(v)
        return ' '.join(ret)

