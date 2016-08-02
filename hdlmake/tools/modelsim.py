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

from .sim_makefile_support import VsimMakefileWriter

XmlImpl = xml.dom.minidom.getDOMImplementation()

MODELSIM_STANDARD_LIBS = ['ieee', 'std', 'altera_mf']


class ToolModelsim(VsimMakefileWriter):

    TOOL_INFO = {
        'name': 'Modelsim',
        'id': 'modelsim',
        'windows_bin': 'vsim',
        'linux_bin': 'vsim'}

    SUPPORTED_FILES = []


    def __init__(self):
        super(ToolModelsim, self).__init__()
        self.vcom_flags.extend(["-modelsimini", "modelsim.ini"])
        self.vlog_flags.extend(["-modelsimini", "modelsim.ini"])
        self.vmap_flags.extend(["-modelsimini", "modelsim.ini"])
        self.copy_rules["modelsim.ini"] = os.path.join(
            "$(MODELSIM_INI_PATH)", "modelsim.ini")
        self.additional_deps.append("modelsim.ini")
        self.additional_clean.extend(
            ["./modelsim.ini", "transcript", "*.vcd", "*.wlf"])

    def detect_version(self, path):
        pass


    def _print_sim_options(self, top_module):
        if top_module.pool.env["modelsim_path"]:
            modelsim_ini_path = os.path.join(
                top_module.pool.env["modelsim_path"],
                "..")
        else:
            modelsim_ini_path = os.path.join("$(HDLMAKE_MODELSIM_PATH)", "..")
        self.custom_variables["MODELSIM_INI_PATH"] = modelsim_ini_path
        super(ToolModelsim, self)._print_sim_options(top_module)


