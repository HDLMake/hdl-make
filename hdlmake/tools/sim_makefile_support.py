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

"""Module providing common stuff for Modelsim, Vsim... like simulators"""

from __future__ import absolute_import
import os
import string

from .make_sim import ToolSim
from hdlmake.util import shell
from hdlmake.srcfile import VerilogFile, VHDLFile, SVFile
import six


class VsimMakefileWriter(ToolSim):

    """A Makefile writer for simulation suitable for vsim based simulators.

    Currently used by:
      - Modelsim
      - Riviera
    """

    HDL_FILES = {VerilogFile: '', VHDLFile: '', SVFile: ''}

    def __init__(self):
        super(VsimMakefileWriter, self).__init__()
        # These are variables that will be set in the makefile
        # The key is the variable name, and the value is the variable value
        self.custom_variables = {}
        # Additional sim dependencies (e.g. modelsim.ini)
        self.additional_deps = []
        # These are files copied into your working directory by a make rule
        # The key is the filename, the value is the file source path
        self.copy_rules = {}
        self._hdl_files.update(VsimMakefileWriter.HDL_FILES)

    def _makefile_sim_options(self):
        """Print the vsim options to the Makefile"""
        def __get_rid_of_vsim_incdirs(vlog_opt=""):
            """Parse the VLOG options and purge the included dirs"""
            if not vlog_opt:
                vlog_opt = ""
            vlogs = vlog_opt.split(' ')
            ret = []
            for vlog_aux in vlogs:
                if not vlog_aux.startswith("+incdir+"):
                    ret.append(vlog_aux)
            return ' '.join(ret)
        vcom_flags = "-quiet " + self.manifest_dict.get("vcom_opt", '')
        vsim_flags = "" + self.manifest_dict.get("vsim_opt", '')
        vlog_flags = "-quiet " + __get_rid_of_vsim_incdirs(
            self.manifest_dict.get("vlog_opt", ''))
        vmap_flags = "" + self.manifest_dict.get("vmap_opt", '')
        for var, value in six.iteritems(self.custom_variables):
            self.writeln("%s := %s" % (var, value))
        self.writeln()
        self.writeln("VCOM_FLAGS := %s" % vcom_flags)
        self.writeln("VSIM_FLAGS := %s" % vsim_flags)
        self.writeln("VLOG_FLAGS := %s" % vlog_flags)
        self.writeln("VMAP_FLAGS := %s" % vmap_flags)

    def _makefile_sim_compilation(self):
        """Write a properly formatted Makefile for the simulator.
        The Makefile format is shared, but flags, dependencies, clean rules,
        etc are defined by the specific tool.
        """
        def __create_copy_rule(name, src):
            """Get a Makefile rule named name, which depends on src,
            copying it to the local directory."""
            rule = """%s: %s
\t\t%s $< . 2>&1
""" % (name, src, shell.copy_command())
            return rule
        fileset = self.fileset
        if self.manifest_dict.get("include_dirs") == None:
            self.writeln("INCLUDE_DIRS :=")
        else:
            self.writeln("INCLUDE_DIRS := +incdir+%s" %
                ('+'.join(self.manifest_dict.get("include_dirs"))))
        libs = set(f.library for f in fileset)
        self.write('LIBS := ')
        self.write(' '.join(libs))
        self.write('\n')
        # tell how to make libraries
        self.write('LIB_IND := ')
        self.write(' '.join([lib + shell.slash_char() +
                   "." + lib for lib in libs]))
        self.write('\n')
        self.writeln()
        self.writeln(
            "simulation: %s $(LIB_IND) $(VERILOG_OBJ) $(VHDL_OBJ)" %
            (' '.join(self.additional_deps)),)
        self.writeln("$(VERILOG_OBJ) : " + ' '.join(self.additional_deps))
        self.writeln(
            "$(VHDL_OBJ): $(LIB_IND) " +
            ' '.join(
                self.additional_deps))
        self.writeln()
        for filename, filesource in six.iteritems(self.copy_rules):
            self.write(__create_copy_rule(filename, filesource))
        for lib in libs:
            self.write(lib + shell.slash_char() + "." + lib + ":\n")
            vmap_command = "vmap $(VMAP_FLAGS)"
            self.write(' '.join(["\t(vlib", lib, "&&", vmap_command, lib, "&&",
                shell.touch_command(), lib + shell.slash_char() +
                "." + lib, ")"]))
            self.write(' '.join(["||", shell.del_command(), lib, "\n"]))
            self.write('\n\n')
        # rules for all _primary.dat files for sv
        for vlog in fileset.filter(VerilogFile):
            if vlog.is_include:
              continue
            self.write("%s: %s" % (os.path.join(
                vlog.library, vlog.purename,
                ".%s_%s" % (vlog.purename, vlog.extension())),
                vlog.rel_path()))
            # list dependencies, do not include the target file
            for dep_file in [dfile for dfile
                             in vlog.depends_on if dfile is not vlog]:
                if dep_file in fileset and not dep_file.is_include:
                    name = dep_file.purename
                    extension = dep_file.extension()
                    self.write(" \\\n" + os.path.join(
                        dep_file.library, name, ".%s_%s" % (name, extension)))
                else:  # the file is included -> we depend directly on the file
                    self.write(" \\\n" + dep_file.rel_path())
            self.writeln()
            compile_template = string.Template(
                "\t\tvlog -work ${library} $$(VLOG_FLAGS) "
                "${sv_option} $${INCLUDE_DIRS} $$<")
            compile_line = compile_template.substitute(
                library=vlog.library, sv_option="-sv"
                if isinstance(vlog, SVFile) else "")
            self.writeln(compile_line)
            self.write("\t\t@" + shell.mkdir_command() + " $(dir $@)")
            self.writeln(" && " + shell.touch_command() + " $@ \n\n")
            self.writeln()
        # list rules for all _primary.dat files for vhdl
        for vhdl in fileset.filter(VHDLFile):
            lib = vhdl.library
            purename = vhdl.purename
            # each .dat depends on corresponding .vhd file
            self.write("%s: %s" % (os.path.join(
                lib, purename, "." + purename + "_" + vhdl.extension()),
                vhdl.rel_path()))
            # list dependencies, do not include the target file
            for dep_file in [dfile for dfile in vhdl.depends_on
                             if dfile is not vhdl]:
                if dep_file in fileset:
                    name = dep_file.purename
                    extension = dep_file.extension()
                    self.write(" \\\n" + os.path.join(dep_file.library,
                               name, ".%s_%s" % (name, extension)))
                else:
                    self.write(" \\\n" + dep_file.rel_path())
            self.writeln()
            self.writeln(' '.join(["\t\tvcom $(VCOM_FLAGS)",
                         "-work", lib, "$< "]))
            self.writeln("\t\t@" + shell.mkdir_command() +
                " $(dir $@) && " + shell.touch_command() + " $@ \n\n")
