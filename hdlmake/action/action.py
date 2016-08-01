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

class Action(object):
    """This is the base class providing the common Action methods"""

    def __init__(self):
        self.top_module = None
        self._deps_solved = False
        self.env = None


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
