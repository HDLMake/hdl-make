#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013, 2014 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Modified to allow ISim simulation by Lucas Russo (lucas.russo@lnls.br)
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

"""Module providing the core functionality for writing Makefiles"""

import os
import string

from .action import Action


class ActionMakefile(Action):
    """Class that provides the Makefile writing methods and status"""

    def __init__(self, filename=None):
        self._file = None
        self._initialized = False
        if filename:
            self._filename = filename
        else:
            self._filename = "Makefile"
        super(ActionMakefile, self).__init__()

    def __del__(self):
        if self._file:
            self._file.close()




    def _print_sim_top(self, top_module):
        top_parameter = string.Template("""TOP_MODULE := ${top_module}\n
PWD := $$(shell pwd)""")
        self.writeln(top_parameter.substitute(
            top_module=top_module.manifest_dict["sim_top"]))

    def _print_syn_top(self, top_module):
        top_parameter = string.Template("""TOP_MODULE := ${top_module}\n
PWD := $$(shell pwd)""")
        self.writeln(top_parameter.substitute(
            top_module=top_module.manifest_dict["syn_top"]))

    def _print_sim_local(self, top_module):
        self.writeln("#target for performing local simulation\n"
                     "local: sim_pre_cmd simulation sim_post_cmd\n")

    def _print_sim_sources(self, fileset):
        from hdlmake.srcfile import VerilogFile, VHDLFile
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
            self.write(
                os.path.join(
                    vl.library,
                    vl.purename,
                    "." +
                    vl.purename +
                    "_" +
                    vl.extension(
                    )) +
                " \\\n")
        self.write('\n')

        self.write("VHDL_SRC := ")
        for vhdl in fileset.filter(VHDLFile):
            self.write(vhdl.rel_path() + " \\\n")
        self.writeln()

        # list vhdl objects (_primary.dat files)
        self.write("VHDL_OBJ := ")
        for vhdl in fileset.filter(VHDLFile):
            # file compilation indicator (important: add _vhd ending)
            self.write(
                os.path.join(
                    vhdl.library,
                    vhdl.purename,
                    "." +
                    vhdl.purename +
                    "_" +
                    vhdl.extension(
                    )) +
                " \\\n")
        self.write('\n')


    def _print_syn_command(self, top_module):
        if top_module.manifest_dict["syn_pre_cmd"]:
            syn_pre_cmd = top_module.manifest_dict["syn_pre_cmd"]
        else:
            syn_pre_cmd = ''

        if top_module.manifest_dict["syn_post_cmd"]:
            syn_post_cmd = top_module.manifest_dict["syn_post_cmd"]
        else:
            syn_post_cmd = ''

        syn_command = string.Template("""# USER SYN COMMANDS
syn_pre_cmd:
\t\t${syn_pre_cmd}
syn_post_cmd:
\t\t${syn_post_cmd}
""")

        self.writeln(syn_command.substitute(syn_pre_cmd=syn_pre_cmd,
                                            syn_post_cmd=syn_post_cmd))


    def _print_sim_command(self, top_module):
        if top_module.manifest_dict["sim_pre_cmd"]:
            sim_pre_cmd = top_module.manifest_dict["sim_pre_cmd"]
        else:
            sim_pre_cmd = ''

        if top_module.manifest_dict["sim_post_cmd"]:
            sim_post_cmd = top_module.manifest_dict["sim_post_cmd"]
        else:
            sim_post_cmd = ''

        sim_command = string.Template("""# USER SIM COMMANDS
sim_pre_cmd:
\t\t${sim_pre_cmd}
sim_post_cmd:
\t\t${sim_post_cmd}
""")

        self.writeln(sim_command.substitute(sim_pre_cmd=sim_pre_cmd,
                                            sim_post_cmd=sim_post_cmd))

    def _print_sim_phony(self, top_module):
        self.writeln(".PHONY: mrproper clean sim_pre_cmd sim_post_cmd simulation")


    def initialize(self):
        """Open the Makefile file and print a header if not initialized"""
        if not self._initialized:
            if os.path.exists(self._filename):
                if os.path.isfile(self._filename):
                    os.remove(self._filename)
                elif os.path.isdir(self._filename):
                    os.rmdir(self._filename)

            self._file = open(self._filename, "a+")
            self._initialized = True
            self.writeln("########################################")
            self.writeln("#  This file was generated by hdlmake  #")
            self.writeln("#  http://ohwr.org/projects/hdl-make/  #")
            self.writeln("########################################")
            self.writeln()
        elif not self._file:
            self._file = open(self._filename, "a+")

    def write(self, line=None):
        """Write a string in the manifest, no new line"""
        if not self._initialized:
            self.initialize()
        self._file.write(line)

    def writeln(self, text=None):
        """Write a string in the manifest, automatically add new line"""
        if text is None:
            self.write("\n")
        else:
            self.write(text + "\n")

