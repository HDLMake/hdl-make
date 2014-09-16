#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013, 2014 CERN
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


import string
from string import Template
import fetch
from makefile_writer import MakefileWriter

import logging


class ToolControls(MakefileWriter):

    def detect_version(self, path):
        pass


    def get_keys(self):
        tool_info = {
            'name': 'GHDL',
            'id': 'ghdl',
            'windows_bin': 'ghdl',
            'linux_bin': 'ghdl'
        }
        return tool_info

    def get_standard_libraries(self):
        GHDL_STANDARD_LIBS = ['ieee', 'std']
        return GHDL_STANDARD_LIBS


    def generate_simulation_makefile(self, fileset, top_module):
        # TODO: vhdl87 vs vhdl97 options
        
        from srcfile import VHDLFile

        makefile_tmplt_1 = string.Template("""TOP_MODULE := ${top_module}
GHDL_CRAP := \
*.cf


#target for performing local simulation
sim: sim_pre_cmd
""")

        makefile_text_1 = makefile_tmplt_1.substitute(
            top_module=top_module.top_module
        )
        self.write(makefile_text_1)

        self.writeln("\t\t# Analyze sources")
        for vhdl in fileset.filter(VHDLFile):
            self.writeln("\t\tghdl -a " + vhdl.rel_path())
        self.writeln()

        self.writeln("\t\t# Elaborate design")
        self.writeln("\t\tghdl -e $(TOP_MODULE)")
        self.writeln()

        makefile_tmplt_2 = string.Template("""      
sim_pre_cmd:
\t\t${sim_pre_cmd}

sim_post_cmd: sim
\t\t${sim_post_cmd}

#target for cleaning all intermediate stuff
clean:
\t\trm -rf $$(GHDL_CRAP)

#target for cleaning final files
mrproper: clean
\t\trm -f *.vcd

.PHONY: mrproper clean sim sim_pre_cmd sim_post_cmd

""")

        if top_module.sim_pre_cmd:
            sim_pre_cmd = top_module.sim_pre_cmd
        else:
            sim_pre_cmd = ''

        if top_module.sim_post_cmd:
            sim_post_cmd = top_module.sim_post_cmd
        else:
            sim_post_cmd = ''

        makefile_text_2 = makefile_tmplt_2.substitute(
            sim_pre_cmd=sim_pre_cmd,
            sim_post_cmd=sim_post_cmd,
        )
        self.write(makefile_text_2)
