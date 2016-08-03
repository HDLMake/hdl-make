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
import string
import logging

from hdlmake.action import ActionMakefile
from hdlmake.util import path as path_mod
from hdlmake.srcfile import (VHDLFile, VerilogFile, SVFile,
                             SignalTapFile, SDCFile, QIPFile, QSYSFile, DPFFile,
                             QSFFile, BSFFile, BDFFile, TDFFile, GDFFile)


QUARTUS_STANDARD_LIBS = ['altera', 'altera_mf', 'lpm', 'ieee', 'std']


class ToolQuartus(ActionMakefile):

    """Class providing the interface for Altera Quartus synthesis"""

    TOOL_INFO = {
        'name': 'Quartus',
        'id': 'quartus',
        'windows_bin': 'quartus',
        'linux_bin': 'quartus',
        'project_ext': 'qsf'}

    SUPPORTED_FILES = [SignalTapFile, SDCFile, QIPFile, QSYSFile, DPFFile,
                       QSFFile, BSFFile, BDFFile, TDFFile, GDFFile]

    CLEAN_TARGETS = {'clean': ["*.rpt", "*.smsg", "run.tcl", "*.summary",
                               "*.done", "*.jdi", "*.pin", "*.qws",
                               "db", "incremental_db"],
                     'mrproper': ["*.sof", "*.pof", "*.jam", "*.jbc",
                                  "*.ekp *.jic"]}

    TCL_CONTROLS = {'windows_interpreter': 'quartus -t ',
                    'linux_interpreter': 'quartus -t ',
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

    def __init__(self):
        self._preflow = None
        self._postmodule = None
        self._postflow = None
        self.properties = []
        self.files = []
        self.filename = None
        super(ToolQuartus, self).__init__()

    def detect_version(self, path):
        """Get Altera Quartus version from the binary program"""
        return 'unknown'

    def _set_tcl_files(self, mod):
        """Method that checks if the TCL files declared by the module
        manifest dictionary exists and if so create them and
        initialize the appropriated variables in the Module instance"""
        if mod.manifest_dict["quartus_preflow"] is not None:
            path = path_mod.compose(
                mod.manifest_dict["quartus_preflow"], mod.path)
            if not os.path.exists(path):
                logging.error("quartus_preflow file listed in " + mod.path +
                              " doesn't exist: " + path + ".\nExiting.")
                quit()
            self._preflow = path
        if mod.manifest_dict["quartus_postmodule"] is not None:
            path = path_mod.compose(
                mod.manifest_dict["quartus_postmodule"], mod.path)
            if not os.path.exists(path):
                logging.error("quartus_postmodule file listed in " + mod.path +
                              " doesn't exist: " + path + ".\nExiting.")
                quit()
            self._postmodule = path
        if mod.manifest_dict["quartus_postflow"] is not None:
            path = path_mod.compose(
                mod.manifest_dict["quartus_postflow"], mod.path)
            if not os.path.exists(path):
                logging.error("quartus_postflow file listed in " + mod.path +
                              " doesn't exist: " + path + ".\nExiting.")
                quit()
            self._postflow = path

    def generate_synthesis_project(
            self, update=False, tool_version='', top_mod=None, fileset=None):
        """Generate an Altera Quartus synthesis project"""
        self.filename = top_mod.manifest_dict["syn_project"]
        self._set_tcl_files(top_mod)
        if update is True:
            self.read()
        else:
            self.add_initial_properties(top_mod)
        self.add_files(fileset)
        self.emit()

    def emit(self):
        """Emit both the QSF and the QPF files with the needed properties"""
        file_aux = open(self.filename + '.qsf', "w")
        for prop in self.properties:
            file_aux.write(prop.emit() + '\n')
        file_aux.write(self.__emit_files())
        file_aux.write(self.__emit_scripts())
        file_aux.close()
        file_aux = open(self.filename + '.qpf', "w")
        file_aux.write("PROJECT_REVISION = \"" + self.filename + "\"\n")
        file_aux.close()

    def __emit_scripts(self):
        """Emit the required TCL scripts to handle the synthesis process"""
        tmp = 'set_global_assignment -name {0} "quartus_sh:{1}"'
        pre = mod = post = ""
        if self._preflow:
            pre = tmp.format(
                "PRE_FLOW_SCRIPT_FILE",
                self._preflow)
        if self._postmodule:
            mod = tmp.format(
                "POST_MODULE_SCRIPT_FILE",
                self._postmodule)
        if self._postflow:
            post = tmp.format(
                "POST_FLOW_SCRIPT_FILE",
                self._postflow)
        return pre + '\n' + mod + '\n' + post + '\n'

    def __emit_files(self):
        """Emit the HDL design files to be added to the project"""
        tmp = "set_global_assignment -name {0} {1}"
        tmplib = tmp + " -library {2}"
        ret = []
        for file_aux in self.files:
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
        return ('\n'.join(ret)) + '\n'

    def add_property(self, val):
        """Add Altera Quartus property to the set of already existing ones"""
        # don't save files (they are unneeded)
        if val.name_type is not None and "_FILE" in val.name_type:
            return
        self.properties.append(val)

    def add_files(self, fileset):
        """Add files to the inner fileset"""
        for file_aux in fileset:
            self.files.append(file_aux)

    def read(self):
        """Read properties from an existing Altera Quartus project file"""

        def __gather_string(words, first_index):
            """Funtion that returns a string from the supplied index"""
            i = first_index
            ret = []
            if words[i][0] != '"':
                return (words[i], 1)
            else:
                while True:
                    ret.append(words[i])
                    if words[i][len(words[i]) - 1] == '"':
                        return (' '.join(ret), len(ret))
                    i = i + 1

        file_aux = open(self.filename + '.qsf', "r")
        lines = [l.strip() for l in file_aux.readlines()]
        lines = [l for l in lines if l != "" and l[0] != '#']
        q_prop = _QuartusProjectProperty
        for line in lines:
            words = line.split()
            command = q_prop.PROP_TYPE[words[0]]
            what = name = name_type = from_ = to_ = section_id = None
            i = 1
            while True:
                if i >= len(words):
                    break

                if words[i] == "-name":
                    name_type = words[i + 1]
                    name, add = __gather_string(words, i + 2)
                    i = i + 2 + add
                    continue
                elif words[i] == "-section_id":
                    section_id, add = __gather_string(words, i + 1)
                    i = i + 1 + add
                    continue
                elif words[i] == "-to":
                    to_, add = __gather_string(words, i + 1)
                    i = i + 1 + add
                    continue
                elif words[i] == "-from":
                    from_, add = __gather_string(words, i + 1)
                    i = i + 2
                    continue
                else:
                    what = words[i]
                    i = i + 1
                    continue
            prop = q_prop(command=command,
                          what=what, name=name,
                          name_type=name_type,
                          from_=from_,
                          to_=to_,
                          section_id=section_id)

            self.add_property(prop)
        file_aux.close()

    def add_initial_properties(self, top_mod):
        """Add initial properties to the Altera Quartus project"""
        import re
        family_names = {
            "^EP2AGX.*$": "Arria II GX",
            "^EP3C.*$": "Cyclone III",
            "^EP4CE.*$": "Cyclone IV E",
            "^EP4CGX.*$": "Cyclone IV GX",
            "^5S.*$": "Stratix V",
        }
        syn_device = top_mod.manifest_dict["syn_device"]
        syn_family = top_mod.manifest_dict["syn_family"]
        syn_grade = top_mod.manifest_dict["syn_grade"]
        syn_package = top_mod.manifest_dict["syn_package"]
        syn_top = top_mod.manifest_dict["syn_top"]
        if syn_family is None:
            for key in family_names:
                if re.match(key, syn_device.upper()):
                    syn_family = family_names[key]
                    logging.debug(
                        "Auto-guessed syn_family to be %s (%s => %s)",
                        syn_family, syn_device, key)
        if syn_family is None:
            logging.error("Could not auto-guess device family, please "
                          "specify in Manifest.py using syn_family!")
            sys.exit("\nExiting")
        devstring = (syn_device + syn_package + syn_grade).upper()
        q_prop = _QuartusProjectProperty
        self.add_property(
            q_prop(q_prop.SET_GLOBAL_ASSIGNMENT,
                   name_type='FAMILY',
                   name='"' + syn_family + '"'))
        self.add_property(
            q_prop(q_prop.SET_GLOBAL_ASSIGNMENT,
                   name_type='DEVICE',
                   name=devstring))
        self.add_property(
            q_prop(q_prop.SET_GLOBAL_ASSIGNMENT,
                   name_type='TOP_LEVEL_ENTITY',
                   name=syn_top))


class _QuartusProjectProperty(object):

    """Class that serves as a container for Altera Quartus properties"""

    SET_GLOBAL_INSTANCE = 0
    SET_INSTANCE_ASSIGNMENT = 1
    SET_LOCATION_ASSIGNMENT = 2
    SET_GLOBAL_ASSIGNMENT = 3

    PROP_TYPE = {"set_global_instance": SET_GLOBAL_INSTANCE,
                 "set_instance_assignment": SET_INSTANCE_ASSIGNMENT,
                 "set_location_assignment": SET_LOCATION_ASSIGNMENT,
                 "set_global_assignment": SET_GLOBAL_ASSIGNMENT}

    def __init__(self, command, what=None, name=None,
                 name_type=None, from_=None, to_=None, section_id=None):
        self.command = command
        self.what = what
        self.name = name
        self.name_type = name_type
        self.from_ = from_
        self.to_ = to_
        self.section_id = section_id

    def emit(self):
        """Emit a formated property from a defined Altera Quartus one"""
        words = []
        words.append(dict([(b, a) for a, b in
                     self.PROP_TYPE.items()])[self.command])
        if self.what is not None:
            words.append(self.what)
        if self.name is not None:
            words.append("-name")
            words.append(self.name_type)
            words.append(self.name)
        if self.from_ is not None:
            words.append("-from")
            words.append(self.from_)
        if self.to_ is not None:
            words.append("-to")
            words.append(self.to_)
        if self.section_id is not None:
            words.append("-section_id")
            words.append(self.section_id)
        return ' '.join(words)
