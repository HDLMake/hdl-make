#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013, 2014 CERN
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

"""Package providing the bridge with the Host O.S. environment"""

from __future__ import print_function
from __future__ import absolute_import
import os
import os.path
import logging

from .util import path as path_mod
import six


class Env(dict):

    """The Env (Environment) is a dictionary containing the environmental
    variables related with HDLMake for a proper use in the Python code"""

    def __init__(self, options):
        dict.__init__(self)
        self.options = options

    def check_tool(self, info_class):
        """Check if the binary is available in the O.S. environment"""
        def _get_path(name):
            """Get the directory in which the tool binary is at Host"""
            location = os.popen(
                path_mod.which_cmd() + " %s" %
                name).read().split('\n', 1)[0].strip()
            logging.debug("location for %s: %s", name, location)
            return os.path.dirname(location)

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
        tool_info = info_class._tool_info
        if path_mod.check_windows():
            bin_name = tool_info['windows_bin']
        else:
            bin_name = tool_info['linux_bin']
        path_key = tool_info['id'] + '_path'
        name = tool_info['name']
        logging.debug("Checking if " + name + " tool is available on PATH")
        self._report_and_set_hdlmake_var(path_key)
        if self[path_key] is not None:
            if _is_in_path(bin_name, self[path_key]):
                logging.info("%s found under HDLMAKE_%s: %s",
                             name, path_key.upper(), self[path_key])
            else:
                logging.warning("%s NOT found under HDLMAKE_%s: %s",
                                name, path_key.upper(), self[path_key])
        else:
            if _check_in_system_path(bin_name):
                self[path_key] = _get_path(bin_name)
                logging.info("%s found in system PATH: %s",
                             name, self[path_key])
            else:
                logging.warning("%s cannnot be found in system PATH", name)

    def _report_and_set_hdlmake_var(self, name):
        """Create a new entry in the Env dictionary and initialize the value
        to the obtained from the O.S. environmental variable if defined"""
        def _get(name):
            """Ask the Host O.S. for the value of an HDLMAKE_(name)
            environmental variable"""
            assert not name.startswith("HDLMAKE_")
            assert isinstance(name, six.string_types)
            name = name.upper()
            return os.environ.get("HDLMAKE_%s" % name)
        name = name.upper()
        val = _get(name)
        if val:
            logging.debug('Environmental variable HDLMAKE_%s is set: "%s".',
                          name, val)
            self[name.lower()] = val
            return True
        else:
            logging.warning("Environmental variable HDLMAKE_%s is not set.",
                            name)
            self[name.lower()] = None
            return False
