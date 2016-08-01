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

import sys
import logging

from hdlmake import new_dep_solver as dep_solver

class Action(list):
    """This is the base class providing the common Action methods"""

    def __init__(self, *args):
        self.top_module = None
        self._deps_solved = False
        self.env = None
        list.__init__(self, *args)


    def _check_all_fetched_or_quit(self):
        """Check if every module in the pool is fetched"""
        if not self.is_everything_fetched():
            logging.error(
                "Fetching must be done before makefile generation.\n"
                "The following modules remains unfetched:\n"
                "%s",
                "\n".join([str(m) for m in self if not m.isfetched])
            )
            quit()

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
        from hdlmake.srcfile import SourceFileSet
        all_manifested_files = SourceFileSet()
        for module in self:
            all_manifested_files.add(module.files)
        logging.debug("End build complete file set")
        return all_manifested_files

    def build_file_set(self, top_entity=None):
        """Build file set with only those files required by the top entity"""
        logging.debug("Begin build file set for %s", top_entity)
        all_files = self.build_complete_file_set()
        if not self._deps_solved:
            dep_solver.solve(all_files)
            self._deps_solved = True
        from hdlmake.srcfile import SourceFileSet
        source_files = SourceFileSet()
        source_files.add(dep_solver.make_dependency_set(all_files, top_entity))
        logging.debug("End build file set")
        return source_files

    def get_top_module(self):
        """Get the Top module from the pool"""
        return self.top_module

    def is_everything_fetched(self):
        """Check if every module is already fetched"""
        if len([m for m in self if not m.isfetched]) == 0:
            return True
        else:
            return False

