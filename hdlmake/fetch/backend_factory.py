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

from git import Git
from svn import Svn
import logging


class Local(object):
    def __init__(self):
        pass

    def fetch(self, module):
        pass


class BackendFactory(object):
    def __init__(self):
        pass

    def get_backend(self, module):
            if module.source == "local":
                return Local()
            else:
                logging.info("Investigating module: " + str(module) +
                             "[parent: " + str(module.parent) + "]")
                if module.source == "svn":
                    return Svn()
                if module.source == "git":
                    return Git()
