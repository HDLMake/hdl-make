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

import logging
from .constants import (LOCAL)


class BackendFactory(object):

    def __init__(self):
        self.backend_table = {}

    def register_backend(self, backend_id, backend):
        """Add a mapping: backend_id -> backend"""
        self.backend_table[backend_id] = backend

    def get_backend(self, module):
        try:
            if module.source != LOCAL:
                logging.info("Investigating module: " + str(module) +
                             "[parent: " + str(module.parent) + "]")
            backend = self.backend_table[module.source]
        except KeyError:
            error_string = "No registered backend found for module: " +\
                str(module) + "\n" +\
                "Registered backends are:\n"
            for backend_id in self.backend_table.iterkeys():
                error_string += "\t%d" % (backend_id)
            logging.error(error_string)
            raise  # this is serious enough we should let the exception keep going
        return backend
