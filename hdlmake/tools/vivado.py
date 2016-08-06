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

"""Module providing support for Xilinx Vivado synthesis"""


from .xilinx import ToolXilinx
from hdlmake.srcfile import (UCFFile, NGCFile, XMPFile,
                             XCOFile, BDFile, TCLFile)


VIVADO_STANDARD_LIBS = ['ieee', 'std']


class ToolVivado(ToolXilinx):

    """Class providing the interface for Xilinx Vivado synthesis"""

    TOOL_INFO = {
        'name': 'vivado',
        'id': 'vivado',
        'windows_bin': 'vivado ',
        'linux_bin': 'vivado ',
        'project_ext': 'xpr'
    }

    SUPPORTED_FILES = [UCFFile, NGCFile, XMPFile,
                       XCOFile, BDFile, TCLFile]

    CLEAN_TARGETS = {'clean': ["run.tcl", ".Xil", "*.jou", "*.log",
                               "$(PROJECT).cache", "$(PROJECT).data",
                               "$(PROJECT).runs", "$(PROJECT_FILE)"]}

    TCL_CONTROLS = {'bitstream': 'launch_runs impl_1 -to_step write_bitstream'
                                 '\n'
                                 'wait_on_run impl_1'}

    def __init__(self):
        super(ToolVivado, self).__init__()
        self._tool_info.update(ToolVivado.TOOL_INFO)
        self._supported_files.extend(ToolVivado.SUPPORTED_FILES)
        self._clean_targets.update(ToolVivado.CLEAN_TARGETS)
        self._tcl_controls.update(ToolVivado.TCL_CONTROLS)

