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
import hdlmake.new_dep_solver as dep_solver

class ListFiles(Action):
    def run(self):
        unfetched_modules = [m for m in self.modules_pool if not m.isfetched]
        for m in unfetched_modules:
            logging.warning("List incomplete, module %s has not been fetched!", m)
        file_set = self.modules_pool.build_file_set()
        file_list = dep_solver.make_dependency_sorted_list(file_set)
        files_str = [f.path for f in file_list]
        if self.options.delimiter == None:
            delimiter = "\n"
        else:
            delimiter = self.options.delimiter
        print(delimiter.join(files_str))
