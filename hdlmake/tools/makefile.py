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

from hdlmake.util import path as path_mod


class ToolMakefile(object):

    """Class that provides the Makefile writing methods and status"""

    def __init__(self, filename=None):
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
        if filename:
            self._filename = filename
        else:
            self._filename = "Makefile"

    def __del__(self):
        if self._file:
            self._file.close()

    def makefile_setup(self, manifest_project_dict, fileset):
        """Set the Makefile configuration"""
        self.manifest_dict = manifest_project_dict
        self.fileset = fileset

    def makefile_check_tool(self, path_key):
        """Check if the binary is available in the O.S. environment"""
        def _get_path(name):
            """Get the directory in which the tool binary is at Host"""
            locations = path_mod.which(name)
            if len(locations) == 0:
                return
            logging.debug("location for %s: %s", name, locations[0])
            return os.path.dirname(locations[0])

        def _is_in_path(name, path=None):
            """Check if the directory is in the system path"""
            if path is not None:
                return os.path.exists(os.path.join(path, name))
            else:
                assert isinstance(name, six.string_types)
                path = _get_path(name)
                return len(path) > 0

        def _check_in_system_path(name):
            """Check if if in the system path exists a file named (name)"""
            path = _get_path(name)
            if path:
                return True
            else:
                return False
        tool_info = self._tool_info
        if path_mod.check_windows():
            bin_name = tool_info['windows_bin']
        else:
            bin_name = tool_info['linux_bin']
        name = tool_info['name']
        logging.debug("Checking if " + name + " tool is available on PATH")
        if path_key in self.manifest_dict:
            if _is_in_path(bin_name, self.manifest_dict[path_key]):
                logging.info("%s found under HDLMAKE_%s: %s",
                             name, path_key.upper(),
                             self.manifest_dict[path_key])
            else:
                logging.warning("%s NOT found under HDLMAKE_%s: %s",
                                name, path_key.upper(),
                                self.manifest_dict[path_key])
                self.manifest_dict[path_key] = ''
        else:
            if _check_in_system_path(bin_name):
                self.manifest_dict[path_key] = _get_path(bin_name)
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
        self.writeln("#target for cleaning intermediate files")
        self.writeln("clean:")
        tmp = "\t\t" + path_mod.del_command() + \
            " $(LIBS) " + ' '.join(self._clean_targets["clean"])
        self.writeln(tmp)

    def makefile_mrproper(self):
        """Print the Makefile target for cleaning final files"""
        self.writeln("#target for cleaning final files")
        self.writeln("mrproper: clean")
        tmp = "\t\t" + path_mod.del_command() + \
            " " + ' '.join(self._clean_targets["mrproper"])
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
        self._file.write(line)

    def writeln(self, text=None):
        """Write a string in the manifest, automatically add new line"""
        if text is None:
            self.write("\n")
        else:
            self.write(text + "\n")
