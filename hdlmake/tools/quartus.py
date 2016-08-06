#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 - 2016 CERN
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

"""Module providing support for Altera Quartus synthesis"""

import os
import sys
import logging

from .make_syn import ToolSyn
from hdlmake.util import path as path_mod
from hdlmake.srcfile import (VHDLFile, VerilogFile, SVFile,
                             SignalTapFile, SDCFile, QIPFile, QSYSFile, DPFFile,
                             QSFFile, BSFFile, BDFFile, TDFFile, GDFFile)


QUARTUS_STANDARD_LIBS = ['altera', 'altera_mf', 'lpm', 'ieee', 'std']


class ToolQuartus(ToolSyn):

    """Class providing the interface for Altera Quartus synthesis"""

    TOOL_INFO = {
        'name': 'Quartus',
        'id': 'quartus',
        'windows_bin': 'quartus -t ',
        'linux_bin': 'quartus -t ',
        'project_ext': 'qsf'}

    SUPPORTED_FILES = [SignalTapFile, SDCFile, QIPFile, QSYSFile, DPFFile,
                       QSFFile, BSFFile, BDFFile, TDFFile, GDFFile]

    HDL_FILES = [VHDLFile, VerilogFile, SVFile]

    CLEAN_TARGETS = {'clean': ["*.rpt", "*.smsg", "run.tcl", "*.summary",
                               "*.done", "*.jdi", "*.pin", "*.qws",
                               "db", "incremental_db"],
                     'mrproper': ["*.sof", "*.pof", "*.jam", "*.jbc",
                                  "*.ekp", "*.jic", "*.qsf", "*.qpf"]}

    TCL_CONTROLS = {'create': 'load_package flow\\n'
                              'project_new $(PROJECT)',
                    'open': 'load_package flow\\n'
                            'project_open $(PROJECT)',
                    'save': '',
                    'close': '',
                    'synthesize': '',
                    'translate': '',
                    'map': '',
                    'par': '',
                    'bitstream': 'execute_flow -compile',
                    'install_source': ''}

    SET_GLOBAL_INSTANCE = 0
    SET_INSTANCE_ASSIGNMENT = 1
    SET_LOCATION_ASSIGNMENT = 2
    SET_GLOBAL_ASSIGNMENT = 3

    PROP_TYPE = {"set_global_instance": SET_GLOBAL_INSTANCE,
                 "set_instance_assignment": SET_INSTANCE_ASSIGNMENT,
                 "set_location_assignment": SET_LOCATION_ASSIGNMENT,
                 "set_global_assignment": SET_GLOBAL_ASSIGNMENT}

    def __init__(self):
        super(ToolQuartus, self).__init__()
        self._tool_info.update(ToolQuartus.TOOL_INFO)
        self._hdl_files.extend(ToolQuartus.HDL_FILES)
        self._supported_files.extend(ToolQuartus.SUPPORTED_FILES)
        self._clean_targets.update(ToolQuartus.CLEAN_TARGETS)
        self._tcl_controls.update(ToolQuartus.TCL_CONTROLS)

    def makefile_syn_tcl(self, top_module):
        """Add initial properties to the Altera Quartus project"""
        import re

        def _emit_property(command, what=None, name=None, name_type=None,
                           from_=None, to_=None, section_id=None):
            """Emit a formated property for Altera Quartus TCL"""
            words = []
            words.append(dict([(b, a) for a, b in
                         self.PROP_TYPE.items()])[command])
            if what is not None:
                words.append(what)
            if name is not None:
                words.append("-name")
                words.append(name_type)
                words.append(name)
            if from_ is not None:
                words.append("-from")
                words.append(from_)
            if to_ is not None:
                words.append("-to")
                words.append(to_)
            if section_id is not None:
                words.append("-section_id")
                words.append(section_id)
            return ' '.join(words)

        def __get_family_string(family=None, device=None):
            """Function that looks for a existing device family name and
            try to guess the value from the device string if not defined"""
            family_names = {
                "^EP2AGX.*$": "Arria II GX",
                "^EP3C.*$": "Cyclone III",
                "^EP4CE.*$": "Cyclone IV E",
                "^EP4CGX.*$": "Cyclone IV GX",
                "^5S.*$": "Stratix V"}
            if family is None:
                for key in family_names:
                    if re.match(key, device.upper()):
                        family = family_names[key]
                        logging.debug(
                            "Auto-guessed syn_family to be %s (%s => %s)",
                            family, device, key)
            if family is None:
                logging.error("Could not auto-guess device family, please "
                              "specify in Manifest.py using syn_family!")
                sys.exit("\nExiting")
            return family

        # Set the core Quartus project properties
        family_string = __get_family_string(
            family=top_module.manifest_dict["syn_family"],
            device=top_module.manifest_dict["syn_device"])
        device_string = (
            top_module.manifest_dict["syn_device"] +
            top_module.manifest_dict["syn_package"] +
            top_module.manifest_dict["syn_grade"]).upper()
        command_list = []
        command_list.append(self._tcl_controls["create"])
        command_list.append(_emit_property(self.SET_GLOBAL_ASSIGNMENT,
                                           name_type='FAMILY',
                                           name='"' + family_string + '"'))
        command_list.append(_emit_property(self.SET_GLOBAL_ASSIGNMENT,
                                           name_type='DEVICE',
                                           name=device_string))
        command_list.append(_emit_property(self.SET_GLOBAL_ASSIGNMENT,
                                           name_type='TOP_LEVEL_ENTITY',
                                           name=top_module.manifest_dict["syn_top"]))
        # Insert the Quartus standard control TCL files
        if top_module.manifest_dict["quartus_preflow"] is not None:
            path = path_mod.compose(
                top_module.manifest_dict["quartus_preflow"], top_module.path)
            if not os.path.exists(path):
                logging.error("quartus_preflow file listed in "
                              + top_module.path + " doesn't exist: "
                              + path + ".\nExiting.")
                quit()
            preflow = '"' + 'quartus_sh:' + path + '"'
            command_list.append(_emit_property(self.SET_GLOBAL_ASSIGNMENT,
                                name_type='PRE_FLOW_SCRIPT_FILE',
                                name=preflow))
        if top_module.manifest_dict["quartus_postmodule"] is not None:
            path = path_mod.compose(
                top_module.manifest_dict["quartus_postmodule"], top_module.path)
            if not os.path.exists(path):
                logging.error("quartus_postmodule file listed in "
                              + top_module.path + " doesn't exist: "
                              + path + ".\nExiting.")
                quit()
            postmodule = '"' + 'quartus_sh:' + path + '"'
            command_list.append(_emit_property(self.SET_GLOBAL_ASSIGNMENT,
                                name_type='POST_MODULE_SCRIPT_FILE',
                                name=postmodule))
        if top_module.manifest_dict["quartus_postflow"] is not None:
            path = path_mod.compose(
                top_module.manifest_dict["quartus_postflow"], top_module.path)
            if not os.path.exists(path):
                logging.error("quartus_postflow file listed in "
                              + top_module.path + " doesn't exist: "
                              + path + ".\nExiting.")
                quit()
            postflow = '"' + 'quartus_sh:' + path + '"'
            command_list.append(_emit_property(self.SET_GLOBAL_ASSIGNMENT,
                                name_type='POST_FLOW_SCRIPT_FILE',
                                name=postflow))
        self._tcl_controls["create"] = '\n'.join(command_list)
        super(ToolQuartus, self).makefile_syn_tcl(top_module)

    def makefile_syn_files(self, fileset):
        """Write the files TCL section of the Makefile"""
        self.writeln("define TCL_FILES")
        tmp = "set_global_assignment -name {0} {1}"
        tmplib = tmp + " -library {2}"
        ret = []
        for file_aux in fileset:
            if isinstance(file_aux, VHDLFile):
                line = tmplib.format("VHDL_FILE",
                                     file_aux.rel_path(), file_aux.library)
            elif isinstance(file_aux, SVFile):
                line = tmplib.format(
                    "SYSTEMVERILOG_FILE",
                    file_aux.rel_path(),
                    file_aux.library)
            elif isinstance(file_aux, VerilogFile):
                line = tmp.format("VERILOG_FILE", file_aux.rel_path())
            elif isinstance(file_aux, SignalTapFile):
                line = tmp.format("SIGNALTAP_FILE", file_aux.rel_path())
            elif isinstance(file_aux, SDCFile):
                line = tmp.format("SDC_FILE", file_aux.rel_path())
            elif isinstance(file_aux, QIPFile):
                line = tmp.format("QIP_FILE", file_aux.rel_path())
            elif isinstance(file_aux, QSYSFile):
                line = tmp.format("QSYS_FILE", file_aux.rel_path())
            elif isinstance(file_aux, DPFFile):
                line = tmp.format("MISC_FILE", file_aux.rel_path())
            elif isinstance(file_aux, QSFFile):
                line = tmp.format("SOURCE_TCL_SCRIPT_FILE",
                                  file_aux.rel_path())
            elif isinstance(file_aux, BSFFile):
                line = tmp.format("BSF_FILE", file_aux.rel_path())
            elif isinstance(file_aux, BDFFile):
                line = tmp.format("BDF_FILE", file_aux.rel_path())
            elif isinstance(file_aux, TDFFile):
                line = tmp.format("AHDL_FILE", file_aux.rel_path())
            elif isinstance(file_aux, GDFFile):
                line = tmp.format("GDF_FILE", file_aux.rel_path())
            else:
                continue
            ret.append(line)
        self.writeln('\n'.join(ret))
        self.writeln("endef")
        self.writeln("export TCL_FILES")
