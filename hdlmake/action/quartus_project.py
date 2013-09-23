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

from __future__ import print_function
import logging
import os
from dependable_file import DependableFile
from action import Action
import dep_solver
from tools.quartus import QuartusProject


class GenerateQuartusProject(Action):
    def run(self):
        if self.env["quartus_path"] is None:
            logging.error("Can't generate a Quartus project. Quartus not found.")
            quit()
        else:
            logging.info("Generating/updating Quartus project.")

        self._check_all_fetched_or_quit()

        if os.path.exists(self.top_module.syn_project) or os.path.exists(self.top_module.syn_project + ".qsf"):
            self._update_existing_quartus_project()
        else:
            self._create_new_quartus_project()

    def _create_new_quartus_project(self):
        top_mod = self.modules_pool.get_top_module()
        fileset = self.modules_pool.build_file_set()
        non_dependable = fileset.inversed_filter(DependableFile)
        fileset.add(non_dependable)

        prj = QuartusProject(top_mod.syn_project)
        prj.add_files(fileset)

        prj.add_initial_properties(top_mod.syn_device,
                                   top_mod.syn_grade,
                                   top_mod.syn_package,
                                   top_mod.syn_top)
        prj.preflow = None
        prj.postflow = None

        prj.emit()

    def _update_existing_quartus_project(self):
        top_mod = self.modules_pool.get_top_module()
        fileset = self.modules_pool.build_file_set()
        non_dependable = fileset.inversed_filter(DependableFile)
        fileset.add(non_dependable)
        prj = QuartusProject(top_mod.syn_project)
        prj.read()
        prj.preflow = None
        prj.postflow = None
        prj.add_files(fileset)
        prj.emit()
