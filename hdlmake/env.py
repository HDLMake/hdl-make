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
import six


class Env(dict):

    """The Env (Environment) is a dictionary containing the environmental
    variables related with HDLMake for a proper use in the Python code"""

    def __init__(self, options):
        dict.__init__(self)
        self.options = options

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
