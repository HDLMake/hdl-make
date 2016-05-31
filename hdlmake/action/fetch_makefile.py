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

from hdlmake import global_mod
from hdlmake.makefile_writer import MakefileWriter
from .action import Action

class GenerateFetchMakefile(Action):

    def _check_manifest(self):
        if not self.top_module.action == "synthesis":
            logging.error("action must be equal to \"synthesis\"")
            sys.exit("Exiting")

        if not self.top_module.syn_project:
            logging.error("syn_project must be set in the manifest.")
            sys.exit("Exiting")


    def run(self):
        pool = self.modules_pool
        logging.info("Generating makefile for fetching modules.")
        if pool.get_fetchable_modules() == []:
            logging.error("There are no fetchable modules. "
                          "No fetch makefile is produced")
            quit()

        self._check_all_fetched_or_quit()
        self._check_manifest()
        makefile_writer = MakefileWriter()
        makefile_writer.generate_fetch_makefile(pool)
        del makefile_writer
        logging.info("Makefile for fetching modules generated.")
