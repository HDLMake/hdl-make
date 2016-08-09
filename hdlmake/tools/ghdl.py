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

"""Module providing support for GHDL simulator"""

import os
import string

from .make_sim import ToolSim
from hdlmake.util import path as path_mod
from hdlmake.srcfile import VHDLFile


class ToolGHDL(ToolSim):

    """Class providing the interface for GHDL simulator"""

    TOOL_INFO = {
        'name': 'GHDL',
        'id': 'ghdl',
        'windows_bin': 'ghdl',
        'linux_bin': 'ghdl'}

    STANDARD_LIBS = ['ieee', 'std']

    HDL_FILES = [VHDLFile]

    CLEAN_TARGETS = {'clean': ["*.cf", "*.o", "$(TOP_MODULE)"],
                     'mrproper': ["*.vcd"]}

    def __init__(self):
        super(ToolGHDL, self).__init__()
        self._tool_info.update(ToolGHDL.TOOL_INFO)
        self._hdl_files.extend(ToolGHDL.HDL_FILES)
        self._clean_targets.update(ToolGHDL.CLEAN_TARGETS)

    def makefile_sim_options(self):
        """Print the GHDL options to the Makefile"""
        if self.top_module.manifest_dict["ghdl_opt"]:
            ghdl_opt = self.top_module.manifest_dict["ghdl_opt"]
        else:
            ghdl_opt = ''
        ghdl_string = string.Template(
            """GHDL_OPT := ${ghdl_opt}\n""")
        self.writeln(ghdl_string.substitute(
            ghdl_opt=ghdl_opt))

    def makefile_sim_compilation(self):
        """Print the GDHL simulation compilation target"""
        fileset = self.fileset
        self.writeln("simulation: $(VERILOG_OBJ) $(VHDL_OBJ)")
        self.writeln("\t\tghdl -e $(TOP_MODULE)")
        self.writeln('\n')
        for file_aux in fileset:
            if any(isinstance(file_aux, file_type)
                   for file_type in self._hdl_files):
                self.write("%s: %s" % (os.path.join(
                    file_aux.library, file_aux.purename,
                    ".%s_%s" % (file_aux.purename, file_aux.extension())),
                    file_aux.rel_path()))
                # list dependencies, do not include the target file
                for dep_file in [dfile for dfile in file_aux.depends_on
                                 if dfile is not file_aux]:
                    if dep_file in fileset:
                        name = dep_file.purename
                        extension = dep_file.extension()
                        self.write(" \\\n" + os.path.join(
                            dep_file.library, name, ".%s_%s" %
                            (name, extension)))
                    else:
                        # the file is included -> we depend directly on it
                        self.write(" \\\n" + dep_file.rel_path())
                self.writeln()
                self.writeln("\t\tghdl -a $<")
                self.write("\t\t@" + path_mod.mkdir_command() + " $(dir $@)")
                self.writeln(" && touch $@ \n")
                self.writeln()

