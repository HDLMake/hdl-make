#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Auckland University of Technology
# Author: William Kamp <william.kamp@aut.ac.nz>
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

from hdlmake.makefile_writer import MakefileWriter

class ToolControls(MakefileWriter):
    def __init__(self):
        super(ToolControls, self).__init__()

    def detect_version(self, path):
        pass

    def get_keys(self):
        tool_info = {
            'name': 'No Tool',
            'id': 'notool',
            'windows_bin': '',
            'linux_bin': ''
        }
        return tool_info

    def get_standard_libraries(self):
        return ["ieee", "std", "altera_mf"]

    def generate_simulation_makefile(self, fileset, top_module):
        pass
