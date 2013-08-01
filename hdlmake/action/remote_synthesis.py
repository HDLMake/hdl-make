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

from action import Action
import logging
import os
import sys
import global_mod
from srcfile import SourceFileFactory


class GenerateRemoteSynthesisMakefile(Action):
    def run(self):
        self._check_all_fetched_or_quit()
        logging.info("Generating makefile for remote synthesis.")

        top_mod = self.modules_pool.get_top_module()

        tcl = self._search_tcl_file()

        if tcl is None:
            self._generate_tcl()
            tcl = "run.tcl"
        files = self.modules_pool.build_very_global_file_list()

        sff = SourceFileFactory()
        files.add(sff.new(tcl, module=None))
        files.add(sff.new(top_mod.syn_project, module=None))

        global_mod.makefile_writer.generate_remote_synthesis_makefile(files=files, name=top_mod.syn_name,
                                                            cwd=os.getcwd(), user=self.env["rsynth_user"],
                                                            server=self.env["rsynth_server"])

    def _check_manifest(self):
        if not self.top_module.action == "synthesis":
            logging.error("action must be equal to \"synthesis\"")
            sys.exit("Exiting")

        if not self.top_module.syn_project:
            logging.error("syn_project must be set in the manifest.")
            sys.exit("Exiting")

    def _search_tcl_file(self, directory=None):
        if directory is None:
            directory = "."
        filenames = os.listdir(directory)
        tcls = []
        for filename in filenames:
            file_parts = filename.split('.')
            if file_parts[len(file_parts)-1] == "tcl":
                tcls.append(filename)
        if len(tcls) == 0:
            return None
        if len(tcls) > 1:
            logging.warning("Multiple tcls in the current directory: " + str(tcls) + "\n" +
                            "Picking the first one: " + tcls[0])
        return tcls[0]

    def _generate_tcl(self):
        f = open("run.tcl", "w")
        f.write("project open " + self.top_module.syn_project + '\n')
        f.write("process run {Generate Programming File} -force rerun_all\n")
        f.close()
