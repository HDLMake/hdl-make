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
import os

from ..common.sim_makefile_support import VsimMakefileWriter

XmlImpl = xml.dom.minidom.getDOMImplementation()

MODELSIM_STANDARD_LIBS = ['ieee', 'std', 'altera_mf']


class ToolControls(VsimMakefileWriter):
    def __init__(self):
        super(ToolControls, self).__init__()

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

    def supported_files(self, fileset):
        from hdlmake.srcfile import SourceFileSet
        sup_files = SourceFileSet()
        return sup_files

    def generate_simulation_makefile(self, fileset, top_module):
        self.vcom_flags.extend(["-modelsimini", "modelsim.ini"])
        self.vlog_flags.extend(["-modelsimini", "modelsim.ini"])
        self.vmap_flags.extend(["-modelsimini", "modelsim.ini"])
        if top_module.pool.env["modelsim_path"]:
            modelsim_ini_path = os.path.join(top_module.pool.env["modelsim_path"], "..")
        else:
            modelsim_ini_path = os.path.join("$(HDLMAKE_MODELSIM_PATH)", "..")
        self.custom_variables["MODELSIM_INI_PATH"] = modelsim_ini_path
        self.additional_deps.append("modelsim.ini")
        self.additional_clean.extend(["./modelsim.ini", "transcript", "*.vcd", "*.wlf"])

        self.copy_rules["modelsim.ini"] = os.path.join("$(MODELSIM_INI_PATH)", "modelsim.ini")
        super(ToolControls, self).generate_simulation_makefile(fileset, top_module)

