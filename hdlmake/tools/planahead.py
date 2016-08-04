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

"""Module providing support for Xilinx PlanAhead synthesis"""

from .xilinx import ToolXilinx
from hdlmake.srcfile import (VHDLFile, VerilogFile, SVFile, TCLFile,
                             UCFFile, NGCFile, XMPFile, XCOFile)


PLANAHEAD_STANDARD_LIBS = ['ieee', 'std']


class ToolPlanAhead(ToolXilinx):

    """Class providing the interface for Xilinx PlanAhead synthesis"""

    TOOL_INFO = {
        'name': 'PlanAhead',
        'id': 'planahead',
        'windows_bin': 'planAhead -mode tcl -source ',
        'linux_bin': 'planAhead -mode tcl -source ',
        'project_ext': 'ppr'}

    SUPPORTED_FILES = [UCFFile, NGCFile, XMPFile, XCOFile]

    CLEAN_TARGETS = {'clean': ["planAhead_*", "planAhead.*", "run.tcl",
                               ".Xil", "$(PROJECT).cache", "$(PROJECT).data",
                               " $(PROJECT).runs", "$(PROJECT).ppr"],
                     'mrproper': ["*.bit", "*.bin"]}

    TCL_CONTROLS = {'create': 'create_project $(PROJECT) ./',
                    'open': 'open_project ./$(PROJECT).ppr',
                    'save': '',
                    'close': 'exit',
                    'synthesize': 'reset_run synth_1\n'
                                  'launch_runs synth_1\n'
                                  'wait_on_run synth_1',
                    'translate': '',
                    'map': '',
                    'par': 'reset_run impl_1\n'
                           'launch_runs impl_1\n'
                           'wait_on_run impl_1',
                    'bitstream': 'launch_runs impl_1 -to_step Bitgen\n'
                                 'wait_on_run impl_1',
                    'install_source': '$(PROJECT).runs/impl_1/$(SYN_TOP).bit'}

    def __init__(self):
        super(ToolPlanAhead, self).__init__()

    def detect_version(self, path):
        """Get the Xilinx PlanAhead program version"""
        return 'unknown'

