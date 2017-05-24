#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
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

"""This module provides the common stuff for the different supported actions"""


from __future__ import print_function
from __future__ import absolute_import
import os
import logging
import sys

from hdlmake.tools import load_syn_tool, load_sim_tool
from hdlmake.util import shell
from hdlmake.util.termcolor import colored
from hdlmake import new_dep_solver as dep_solver
from hdlmake.srcfile import SourceFileSet


def set_logging_level(options):
    """Set the log level and config (A.K.A. log verbosity)"""
    numeric_level = getattr(logging, options.log.upper(), None)
    if not isinstance(numeric_level, int):
        sys.exit('Invalid log level: %s' % options.log)

    if not shell.check_windows():
        logging.basicConfig(
            format=colored(
                "%(levelname)s",
                "yellow") + colored(
                "\t%(filename)s:%(lineno)d: %(funcName)s()\t",
                "blue") + "%(message)s",
            level=numeric_level)
    else:
        logging.basicConfig(
            format="%(levelname)s" +
                   "\t%(filename)s:%(lineno)d: %(funcName)s()\t" +
                   "%(message)s",
            level=numeric_level)
    logging.debug(str(options))


class Action(list):

    """This is the base class providing the common Action methods"""

    def __init__(self, options):
        super(Action, self).__init__()
        self.top_module = None
        self.parseable_fileset = SourceFileSet()
        self.privative_fileset = SourceFileSet()
        self._deps_solved = False
        self.options = options
        set_logging_level(options)
        self.new_module(parent=None,
                         url=os.getcwd(),
                         source=None,
                         fetchto=".")
        self.config = self._get_config_dict()
        action = self.config.get("action")
        if action == None:
            self.tool = None
            self.top_entity = None
        elif action == "simulation":
            self.tool = load_sim_tool(self.config.get("sim_tool"))
            self.top_entity = self.config.get("sim_top")
        elif action == "synthesis":
            self.tool = load_syn_tool(self.config.get("syn_tool"))
            self.top_entity = self.config.get("syn_top")
        else:
            logging.error("Unknown requested action: %s", action)
            quit()

    def new_module(self, parent, url, source, fetchto):
        """Add new module to the pool.

        This is the only way to add new modules to the pool
        Thanks to it the pool can easily control its content

        NOTE: the first module added to the pool will become the top_module!.
        """
        from hdlmake.module import Module, ModuleArgs
        self._deps_solved = False
        new_module_args = ModuleArgs()
        new_module_args.set_args(parent, url, source, fetchto)
        new_module = Module(new_module_args, self)
        if not self.__contains(new_module):
            self._add(new_module)
            if not self.top_module:
                self.top_module = new_module
                new_module.parse_manifest()
        return new_module

    def _check_manifest_variable_is_set(self, name):
        """Method to check if a specific manifest variable is set"""
        if getattr(self.top_module, name) is None:
            logging.error(
                "Variable %s must be set in the manifest "
                "to perform current action (%s)",
                name, self.__class__.__name__)
            sys.exit("\nExiting")

    def _check_manifest_variable_value(self, name, value):
        """Method to check if a manifest variable is set to a specific value"""
        variable_match = False
        manifest_value = getattr(self.top_module, name)
        if manifest_value == value:
            variable_match = True

        if variable_match is False:
            logging.error(
                "Variable %s must be set in the manifest and equal to '%s'.",
                name, value)
            sys.exit("Exiting")

    def build_complete_file_set(self):
        """Build file set with all the files listed in the complete pool"""
        logging.debug("Begin build complete file set")
        all_manifested_files = SourceFileSet()
        for module in self:
            all_manifested_files.add(module.files)
        logging.debug("End build complete file set")
        return all_manifested_files

    def solve_file_set(self):
        """Build file set with only those files required by the top entity"""
        if not self._deps_solved:
            dep_solver.solve(self.parseable_fileset,
                             self.tool.get_standard_libs())
            self._deps_solved = True
        solved_files = SourceFileSet()
        solved_files.add(dep_solver.make_dependency_set(
            self.parseable_fileset, self.top_entity))
        self.parseable_fileset = solved_files

    def build_file_set(self):
        """Initialize the parseable and privative fileset contents"""
        total_files = self.build_complete_file_set()
        for file_aux in total_files:
            if any(isinstance(file_aux, file_type)
                   for file_type in self.tool.get_privative_files()):
                self.privative_fileset.add(file_aux)
            elif any(isinstance(file_aux, file_type)
                   for file_type in self.tool.get_parseable_files()):
                self.parseable_fileset.add(file_aux)
            else:
                logging.error("File not supported by the tool: %s",
                              file_aux.path)
        if len(self.privative_fileset) > 0:
            logging.info("Detected %d supported files that are not parseable",
                         len(self.privative_fileset))
        if len(self.parseable_fileset) > 0:
            logging.info("Detected %d supported files that can be parsed",
                         len(self.parseable_fileset))

    def get_top_module(self):
        """Get the Top module from the pool"""
        return self.top_module

    def _get_config_dict(self):
        """Get the combined hierarchical Manifest dictionary from the pool"""
        config_dict = {}
        for mod in self:
            manifest_dict_tmp = mod.manifest_dict
            if not manifest_dict_tmp == None:
                if 'fetchto' in manifest_dict_tmp:
                    manifest_dict_tmp['fetchto'] = os.path.relpath(os.path.join(
                        mod.path,
                        mod.manifest_dict['fetchto']))
                manifest_dict_tmp.update(config_dict)
                config_dict = manifest_dict_tmp
        return config_dict

    def _add(self, new_module):
        """Add the given new module if this is not already in the pool"""
        from hdlmake.module import Module
        if not isinstance(new_module, Module):
            raise RuntimeError("Expecting a Module instance")
        if self.__contains(new_module):
            return False
        if new_module.isfetched:
            for mod in new_module.submodules():
                self._add(mod)
        self.append(new_module)
        return True

    def __contains(self, module):
        """Check if the pool contains the given module by checking the URL"""
        for mod in self:
            if mod.url == module.url:
                return True
        return False

    def __str__(self):
        """Cast the module list as a list of strings"""
        return str([str(m) for m in self])
