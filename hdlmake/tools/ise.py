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

"""Module providing the classes that are used to handle Xilinx ISE"""

from __future__ import print_function
from __future__ import absolute_import
import logging

from .make_syn import ToolSyn

from hdlmake.srcfile import (VHDLFile, VerilogFile, SVFile,
                             UCFFile, CDCFile, NGCFile)

FAMILY_NAMES = {
    "XC6S": "Spartan6",
    "XC3S": "Spartan3",
    "XC6V": "Virtex6",
    "XC5V": "Virtex5",
    "XC4V": "Virtex4",
    "XC7Z": "Zynq",
    "XC7V": "Virtex7",
    "XC7K": "Kintex7",
    "XC7A": "Artix7"}

ISE_STANDARD_LIBS = ['ieee', 'ieee_proposed', 'iSE', 'simprims', 'std',
                     'synopsys', 'unimacro', 'unisim', 'XilinxCoreLib']


class ToolISE(ToolSyn):

    """Class providing the methods to create and build a Xilinx ISE project"""

    TOOL_INFO = {
        'name': 'ISE',
        'id': 'ise',
        'windows_bin': 'xtclsh',
        'linux_bin': 'xtclsh',
        'project_ext': 'xise'}

    STANDARD_LIBS = ['ieee', 'ieee_proposed', 'iSE', 'simprims', 'std',
                     'synopsys', 'unimacro', 'unisim', 'XilinxCoreLib']

    SUPPORTED_FILES = [UCFFile, CDCFile, NGCFile]

    HDL_FILES = [VHDLFile, VerilogFile, SVFile]

    CLEAN_TARGETS = {'clean': ["xst xlnx_auto_*_xdb", "iseconfig _xmsgs",
                               "_ngo", "*.b", "*_summary.html", "*.tcl",
                               "*.bld", "*.cmd_log", "*.drc", "*.lso", "*.ncd",
                               "*.ngc", "*.ngd", "*.ngr", "*.pad", "*.par",
                               "*.pcf", "*.prj", "*.ptwx", "*.stx", "*.syr",
                               "*.twr", "*.twx", "*.gise", "*.gise", "*.bgn",
                               "*.unroutes", "*.ut", "*.xpi", "*.xst",
                               "*.xise", "*.xwbt",
                               "*_envsettings.html", "*_guide.ncd",
                               "*_map.map", "*_map.mrp", "*_map.ncd",
                               "*_map.ngm", "*_map.xrpt", "*_ngdbuild.xrpt",
                               "*_pad.csv", "*_pad.txt", "*_par.xrpt",
                               "*_summary.xml", "*_usage.xml", "*_xst.xrpt",
                               "usage_statistics_webtalk.html", "webtalk.log",
                               "par_usage_statistics.html", "webtalk_pn.xml",
                               "run_synthesize.tcl", "run_translate.tcl",
                               "run_map.tcl", "run_par.tcl",
                               "run_bitstream.tcl"],
                     'mrproper': ["*.bit", "*.bin", "*.mcs"]}

    TCL_CONTROLS = {'create': 'project new $(PROJECT_FILE)',
                    'open': 'project open $(PROJECT_FILE)',
                    'save': 'project save',
                    'close': 'project close',
                    'synthesize': 'process run {Synthesize - XST}',
                    'translate': 'process run {Translate}',
                    'map': 'process run {Map}',
                    'par': 'process run {Place & Route}',
                    'bitstream': 'process run {Generate Programming File}',
                    'install_source': '*.bit *.bin'}

    def __init__(self):
        super(ToolISE, self).__init__()
        self._tool_info.update(ToolISE.TOOL_INFO)
        self._hdl_files.extend(ToolISE.HDL_FILES)
        self._supported_files.extend(ToolISE.SUPPORTED_FILES)
        self._standard_libs.extend(ToolISE.STANDARD_LIBS)
        self._clean_targets.update(ToolISE.CLEAN_TARGETS)
        self._tcl_controls.update(ToolISE.TCL_CONTROLS)

    def makefile_syn_tcl(self):
        """Create a Xilinx synthesis project by TCL"""
        top_module = self.top_module
        tmp = "{0}set {1} {2}"
        syn_device = top_module.manifest_dict["syn_device"]
        syn_grade = top_module.manifest_dict["syn_grade"]
        syn_package = top_module.manifest_dict["syn_package"]
        syn_family = top_module.manifest_dict["syn_family"]
        if syn_family is None:
            syn_family = FAMILY_NAMES.get(
                top_module.manifest_dict["syn_device"][0:4].upper())
            if syn_family is None:
                logging.error(
                    "syn_family is not definied in Manifest.py"
                    " and can not be guessed!")
                quit(-1)
        create_new = []
        create_new.append(self._tcl_controls["create"])
        properties = [
            ['project ', 'family', syn_family],
            ['project ', 'device', syn_device],
            ['project ', 'package', syn_package],
            ['project ', 'speed', syn_grade],
            ['project ', '"Manual Implementation Compile Order"', '"false"'],
            ['project ', '"Auto Implementation Top"', '"false"'],
            ['project ', '"Create Binary Configuration File"', '"true"'],
            ['', 'compile_directory', '.']]
        for prop in properties:
            create_new.append(tmp.format(prop[0], prop[1], prop[2]))
        self._tcl_controls["create"] = "\n".join(create_new)
        super(ToolISE, self).makefile_syn_tcl()

    def makefile_syn_files(self):
        """Write the files TCL section of the Makefile"""
        hdl = "xfile add {0}"
        self.writeln("define TCL_FILES")
        for file_aux in self.fileset:
            self.writeln(hdl.format(file_aux.rel_path()))
        self.writeln("project set top $(TOP_MODULE)")
        self.writeln("endef")
        self.writeln("export TCL_FILES")
