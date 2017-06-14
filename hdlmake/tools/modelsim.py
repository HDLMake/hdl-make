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

"""Module providing support for Mentor Modelsim simulation"""

from __future__ import print_function
from __future__ import absolute_import
import os

from .sim_makefile_support import VsimMakefileWriter


class ToolModelsim(VsimMakefileWriter):

    """Class providing the interface for Mentor Modelsim simulator"""

    TOOL_INFO = {'name': 'Modelsim',
                 'id': 'modelsim',
                 'windows_bin': 'vsim.exe',
                 'linux_bin': 'vsim'}

    STANDARD_LIBS = ['ieee', 'std', 'altera_mf']

    CLEAN_TARGETS = {'clean': ["modelsim.ini", "transcript"],
                     'mrproper': ["*.vcd", "*.wlf"]}

    def __init__(self):
        super(ToolModelsim, self).__init__()
        self.copy_rules["modelsim.ini"] = os.path.join(
            "$(MODELSIM_INI_PATH)", "modelsim.ini")
        self.additional_deps.append("modelsim.ini")
        self._tool_info.update(ToolModelsim.TOOL_INFO)
        self._clean_targets.update(ToolModelsim.CLEAN_TARGETS)
        self._standard_libs.extend(ToolModelsim.STANDARD_LIBS)

    def _makefile_sim_options(self):
        """Print the Modelsim options to the Makefile"""
        modelsim_ini_path = self.manifest_dict.get("modelsim_ini_path")
        if modelsim_ini_path == None:
            if "sim_path" in self.manifest_dict:
                modelsim_ini_path = os.path.join(
                    self.manifest_dict["sim_path"], "..")
            else:
                modelsim_ini_path = os.path.join(
                    "$(HDLMAKE_MODELSIM_PATH)", "..")
        self.custom_variables["MODELSIM_INI_PATH"] = modelsim_ini_path
        modelsim_ini = "-modelsimini modelsim.ini "
        vcom_opt = self.manifest_dict.get("vcom_opt", '')
        self.manifest_dict["vcom_opt"] = modelsim_ini + vcom_opt
        vlog_opt = self.manifest_dict.get("vlog_opt", '')
        self.manifest_dict["vlog_opt"] = modelsim_ini + vlog_opt
        vmap_opt = self.manifest_dict.get("vmap_opt", '')
        self.manifest_dict["vmap_opt"] = modelsim_ini + vmap_opt
        super(ToolModelsim, self)._makefile_sim_options()
