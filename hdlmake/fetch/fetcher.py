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

"""Module providing the base class for the different code fetchers"""

from __future__ import absolute_import
import os
from hdlmake.util import shell


class Fetcher(object):

    """Base class for the code fetcher objects"""

    def fetch(self, module):
        """Stub method, this must be implemented by the code fetcher"""
        pass

    @staticmethod
    def check_id(path, command):
        """Use the provided command to get the specific ID from
        the repository at path"""
        cur_dir = os.getcwd()
        os.chdir(path)
        identifier = shell.run(command)
        os.chdir(cur_dir)
        return identifier
