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

from .action import Action
import logging

class ListFiles(Action):
    def run(self):
        unfetched_modules = False
        files_str = []
        for m in self.modules_pool:
            if not m.isfetched:
                unfetched_modules = True
            else:
                files_str.append(self.options.delimiter.join([f.path for f in m.files]))
        if unfetched_modules: logging.warning("Some of the modules have not been fetched!")
        print(" ".join(files_str))
