#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013, 2014 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Modified to allow ISim simulation by Lucas Russo (lucas.russo@lnls.br)
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

"""Module providing the core functionality for writing Makefiles"""

from __future__ import absolute_import
import os
import logging
import six

from hdlmake.util import shell


class ToolMakefile(object):

    """Class that provides the Makefile writing methods and status"""

    def __init__(self):
        super(ToolMakefile, self).__init__()
        self._file = None
        self._initialized = False
        self._tool_info = {}
        self._clean_targets = {}
        self._tcl_controls = {}
        self._hdl_files = {}
        self._supported_files = {}
        self._standard_libs = []
        self.fileset = None
        self.manifest_dict = {}
        self._filename = "Makefile"

    def __del__(self):
        if self._file:
            self._file.close()

    def get_standard_libs(self):
        """Get the standard libs supported by the tool"""
        return self._standard_libs

    def get_parseable_files(self):
        """Get the parseable HDL file types supported by the tool"""
        return self._hdl_files

    def get_privative_files(self):
        """Get the privative format file types supported by the tool"""
        return self._supported_files

    def makefile_setup(self, manifest_project_dict, fileset, filename=None):
        """Set the Makefile configuration"""
        self.manifest_dict = manifest_project_dict
        self.fileset = fileset
        if filename:
            self._filename = filename

    def _get_name_bin(self):
        """Get the name and binary values"""
        if shell.check_windows():
            bin_name = self._tool_info['windows_bin']
        else:
            bin_name = self._tool_info['linux_bin']
        return bin_name

    def _get_path(self):
        """Get the directory in which the tool binary is at Host"""
        bin_name = self._get_name_bin()
        locations = shell.which(bin_name)
        if len(locations) == 0:
            return
        logging.debug("location for %s: %s", bin_name, locations[0])
        return os.path.dirname(locations[0])

    def _is_in_path(self, path_key):
        """Check if the directory is in the system path"""
        path = self.manifest_dict.get(path_key)
        bin_name = self._get_name_bin()
        if path is not None:
            return os.path.exists(os.path.join(path, bin_name))
        else:
            assert isinstance(bin_name, six.string_types)
            path = self._get_path()
            return len(path) > 0

    def _check_in_system_path(self):
        """Check if if in the system path exists a file named (name)"""
        path = self._get_path()
        if path:
            return True
        else:
            return False

    def makefile_check_tool(self, path_key):
        """Check if the binary is available in the O.S. environment"""
        name = self._tool_info['name']
        logging.debug("Checking if " + name + " tool is available on PATH")
        if path_key in self.manifest_dict:
            if self._is_in_path(path_key):
                logging.info("%s found under HDLMAKE_%s: %s",
                             name, path_key.upper(),
                             self.manifest_dict[path_key])
            else:
                logging.warning("%s NOT found under HDLMAKE_%s: %s",
                                name, path_key.upper(),
                                self.manifest_dict[path_key])
                self.manifest_dict[path_key] = ''
        else:
            if self._check_in_system_path():
                self.manifest_dict[path_key] = self._get_path()
                logging.info("%s found in system PATH: %s",
                             name, self.manifest_dict[path_key])
            else:
                logging.warning("%s cannnot be found in system PATH", name)
                self.manifest_dict[path_key] = ''

    def makefile_includes(self):
        """Add the included makefiles that need to be previously loaded"""
        #for file_aux in self.top_module.incl_makefiles:
        #    if os.path.exists(file_aux):
        #        self.write("include %s\n" % file_aux)
        pass

    def makefile_clean(self):
        """Print the Makefile target for cleaning intermediate files"""
        self.writeln("CLEAN_TARGETS := $(LIBS) " +
            ' '.join(self._clean_targets["clean"]) + "\n")
        self.writeln("clean:")
        tmp = "\t\t" + shell.del_command() + " $(CLEAN_TARGETS)"
        self.writeln(tmp)
        if shell.check_windows():
            tmp = "\t\t@-" + shell.rmdir_command() + \
            " $(CLEAN_TARGETS) >nul 2>&1"
            self.writeln(tmp)

    def makefile_mrproper(self):
        """Print the Makefile target for cleaning final files"""
        self.writeln("mrproper: clean")
        tmp = "\t\t" + shell.del_command() + \
            " " + ' '.join(self._clean_targets["mrproper"]) + "\n"
        self.writeln(tmp)

    def initialize(self):
        """Open the Makefile file and print a header if not initialized"""
        if not self._initialized:
            if os.path.exists(self._filename):
                if os.path.isfile(self._filename):
                    os.remove(self._filename)
                elif os.path.isdir(self._filename):
                    os.rmdir(self._filename)

            self._file = open(self._filename, "a+")
            self._initialized = True
            self.writeln("########################################")
            self.writeln("#  This file was generated by hdlmake  #")
            self.writeln("#  http://ohwr.org/projects/hdl-make/  #")
            self.writeln("########################################")
            self.writeln()
        elif not self._file:
            self._file = open(self._filename, "a+")

    def write(self, line=None):
        """Write a string in the manifest, no new line"""
        if not self._initialized:
            self.initialize()
        if shell.check_windows():
            self._file.write(line.replace('\\"', '"'))
        else:
            self._file.write(line)

    def writeln(self, text=None):
        """Write a string in the manifest, automatically add new line"""
        if text is None:
            self.write("\n")
        else:
            self.write(text + "\n")
