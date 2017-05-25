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

from __future__ import absolute_import
import os
import sys
import logging

from .make_syn import ToolSyn
from hdlmake.util import path as path_mod
from hdlmake.util import shell
from hdlmake.srcfile import (VHDLFile, VerilogFile, SVFile, DPFFile,
                             SignalTapFile, SDCFile, QIPFile, QSYSFile,
                             QSFFile, BSFFile, BDFFile, TDFFile, GDFFile)


class ToolQuartus(ToolSyn):

    """Class providing the interface for Altera Quartus synthesis"""

    TOOL_INFO = {
        'name': 'Quartus',
        'id': 'quartus',
        'windows_bin': 'quartus_sh.exe -t',
        'linux_bin': 'quartus_sh -t',
        'project_ext': 'qpf'}

    STANDARD_LIBS = ['altera', 'altera_mf', 'lpm', 'ieee', 'std']

    _QUARTUS_SOURCE = 'set_global_assignment -name {0} $(sourcefile)'

    SUPPORTED_FILES = {
        SignalTapFile: _QUARTUS_SOURCE.format('SIGNALTAP_FILE'),
        SDCFile: _QUARTUS_SOURCE.format('SDC_FILE'),
        QIPFile: _QUARTUS_SOURCE.format('QIP_FILE'),
        QSYSFile: _QUARTUS_SOURCE.format('QSYS_FILE'),
        DPFFile: _QUARTUS_SOURCE.format('MISC_FILE'),
        QSFFile: _QUARTUS_SOURCE.format('SOURCE_TCL_SCRIPT_FILE'),
        BSFFile: _QUARTUS_SOURCE.format('BSF_FILE'),
        BDFFile: _QUARTUS_SOURCE.format('BDF_FILE'),
        TDFFile: _QUARTUS_SOURCE.format('AHDL_FILE'),
        GDFFile: _QUARTUS_SOURCE.format('GDF_FILE')}

    _QUARTUS_LIBRARY = " -library {0}".format('work')

    HDL_FILES = {
        VHDLFile: _QUARTUS_SOURCE.format('VHDL_FILE') +
                  _QUARTUS_LIBRARY,
        VerilogFile: _QUARTUS_SOURCE.format('SYSTEMVERILOG_FILE') +
                     _QUARTUS_LIBRARY,
        SVFile: _QUARTUS_SOURCE.format('VERILOG_FILE') +
                 _QUARTUS_LIBRARY}

    CLEAN_TARGETS = {'clean': ["*.rpt", "*.smsg", "*.summary",
                               "*.done", "*.jdi", "*.pin", "*.qws",
                               "db", "incremental_db", "$(PROJECT).qsf",
                               "*.qpf"],
                     'mrproper': ["*.sof", "*.pof", "*.jam", "*.jbc",
                                  "*.ekp", "*.jic"]}

    TCL_CONTROLS = {'create': 'project_new $(PROJECT)',
                    'open': 'project_open $(PROJECT)',
                    'project': 'load_package flow\n'
                               '$(TCL_CREATE)\n'
                               'source files.tcl',
                    'bitstream': 'load_package flow\n'
                                 '$(TCL_OPEN)\n'
                                 'execute_flow -compile',
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
        self._hdl_files.update(ToolQuartus.HDL_FILES)
        self._supported_files.update(ToolQuartus.SUPPORTED_FILES)
        self._standard_libs.extend(ToolQuartus.STANDARD_LIBS)
        self._clean_targets.update(ToolQuartus.CLEAN_TARGETS)
        self._tcl_controls.update(ToolQuartus.TCL_CONTROLS)

    def _makefile_syn_top(self):
        """Update project synthesis variables for Quartus"""
        import re

        def __get_family_string(family=None, device=None):
            """Function that looks for a existing device family name and
            try to guess the value from the device string if not defined"""
            family_names = {
                "^EP2AGX.*$": "Arria II GX",
                "^EP3C.*$": "Cyclone III",
                "^EP4CE.*$": "Cyclone IV E",
                "^EP4CGX.*$": "Cyclone IV GX",
                "^5A.*$": "Arria V",
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

        family_string = __get_family_string(
            family=self.manifest_dict.get("syn_family", None),
            device=self.manifest_dict.get("syn_device", ''))
        device_string = (self.manifest_dict["syn_device"] +
                         self.manifest_dict["syn_package"] +
                         self.manifest_dict["syn_grade"])
        self.manifest_dict["syn_family"] = family_string
        self.manifest_dict["syn_device"] = device_string
        super(ToolQuartus, self)._makefile_syn_top()

    def _emit_property(self, command, new_property):
        """Emit a formated property for Altera Quartus TCL"""
        property_dict = {
            'what': None,
            'name': None,
            'name_type': None,
            'from_': None,
            'to_': None,
            'section_id': None,
            'tag_': None}
        property_dict.update(new_property)
        words = []
        words.append(dict([(b, a) for a, b in
                     self.PROP_TYPE.items()])[command])
        if property_dict['what'] is not None:
            words.append(property_dict['what'])
        if property_dict['name'] is not None:
            words.append("-name")
            words.append(property_dict['name_type'])
            words.append(property_dict['name'])
        if property_dict['from_'] is not None:
            words.append("-from")
            words.append(property_dict['from_'])
        if property_dict['tag_'] is not None:
            words.append("-tag")
            words.append(property_dict['to_'])
        if property_dict['to_'] is not None:
            words.append("-to")
            words.append(property_dict['to_'])
        if property_dict['section_id'] is not None:
            words.append("-section_id")
            words.append(property_dict['section_id'])
        return ' '.join(words)

    def _makefile_syn_tcl(self):
        """Add initial properties to the Altera Quartus project"""
        command_list = []
        command_list.append(self._tcl_controls["project"])
        command_list.append(self._emit_property(
            self.SET_GLOBAL_ASSIGNMENT,
            {'name_type': 'FAMILY',
            'name': '\\"$(SYN_FAMILY)\\"'}))
        command_list.append(self._emit_property(
            self.SET_GLOBAL_ASSIGNMENT,
            {'name_type': 'DEVICE',
            'name':'\\"$(SYN_DEVICE)\\"'}))
        command_list.append(self._emit_property(
            self.SET_GLOBAL_ASSIGNMENT,
            {'name_type': 'TOP_LEVEL_ENTITY',
            'name': '\\"$(TOP_MODULE)\\"'}))
        self._tcl_controls["project"] = '\n'.join(command_list)
        super(ToolQuartus, self)._makefile_syn_tcl()

    def _makefile_syn_files(self):
        # Insert the Quartus standard control TCL files
        command_list = []
        if "quartus_preflow" in self.manifest_dict:
            path = shell.tclpath(path_mod.compose(
                self.manifest_dict["quartus_preflow"], os.getcwd()))
            if not os.path.exists(path):
                logging.error("quartus_preflow file listed in "
                              + os.getcwd() + " doesn't exist: "
                              + path + ".\nExiting.")
                quit()
            preflow = '"' + 'quartus_sh:' + path + '"'
            command_list.append(self._emit_property(self.SET_GLOBAL_ASSIGNMENT,
                                {'name_type': 'PRE_FLOW_SCRIPT_FILE',
                                'name': preflow}))
        if "quartus_postmodule" in self.manifest_dict:
            path = shell.tclpath(path_mod.compose(
                self.manifest_dict["quartus_postmodule"],
                os.getcwd()))
            if not os.path.exists(path):
                logging.error("quartus_postmodule file listed in "
                              + os.getcwd() + " doesn't exist: "
                              + path + ".\nExiting.")
                quit()
            postmodule = '"' + 'quartus_sh:' + path + '"'
            command_list.append(self._emit_property(self.SET_GLOBAL_ASSIGNMENT,
                                {'name_type': 'POST_MODULE_SCRIPT_FILE',
                                'name': postmodule}))
        if "quartus_postflow" in self.manifest_dict:
            path = shell.tclpath(path_mod.compose(
                self.manifest_dict["quartus_postflow"], os.getcwd()))
            if not os.path.exists(path):
                logging.error("quartus_postflow file listed in "
                              + os.getcwd() + " doesn't exist: "
                              + path + ".\nExiting.")
                quit()
            postflow = '"' + 'quartus_sh:' + path + '"'
            command_list.append(self._emit_property(self.SET_GLOBAL_ASSIGNMENT,
                                {'name_type': 'POST_FLOW_SCRIPT_FILE',
                                'name': postflow}))
        self._tcl_controls["files"] = '\n'.join(command_list)
        super(ToolQuartus, self)._makefile_syn_files()
