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

import string
from hdlmake.action import ActionMakefile
from hdlmake.srcfile import VHDLFile

GHDL_STANDARD_LIBS = ['ieee', 'std']


class ToolGHDL(ActionMakefile):

    """Class providing the interface for Lattice Diamond synthesis"""

    TOOL_INFO = {
        'name': 'GHDL',
        'id': 'ghdl',
        'windows_bin': 'ghdl',
        'linux_bin': 'ghdl'}

    SUPPORTED_FILES = []

    CLEAN_TARGETS = {'clean': ["*.cf", "*.o", "$(TOP_MODULE)"],
                     'mrproper': ["*.vcd"]}

    def __init__(self):
        super(ToolGHDL, self).__init__()

    def detect_version(self, path):
        """Get tool version for GHDL"""
        pass

    def _print_sim_options(self, top_module):
        """Print the GHDL options to the Makefile"""
        if top_module.manifest_dict["ghdl_opt"]:
            ghdl_opt = top_module.manifest_dict["ghdl_opt"]
        else:
            ghdl_opt = ''
        ghdl_string = string.Template(
            """GHDL_OPT := ${ghdl_opt}\n""")
        self.writeln(ghdl_string.substitute(
            ghdl_opt=ghdl_opt))

    def _print_sim_compilation(self, fileset, top_module):
        """Print the GDHL simulation compilation target"""
        self.writeln("simulation:")
        self.writeln("\t\t# Analyze sources")
        for vhdl in fileset.filter(VHDLFile):
            self.writeln("\t\tghdl -a " + vhdl.rel_path())
        self.writeln()
        self.writeln("\t\t# Elaborate design")
        self.writeln("\t\tghdl -e $(TOP_MODULE)")
        self.writeln()
