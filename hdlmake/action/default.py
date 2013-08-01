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
import sys

from action import Action
from simulation import GenerateSimulationMakefile
from ise_project import GenerateISEProject
from quartus_project import GenerateQuartusProject
from ise_makefile import GenerateISEMakefile
from remote_synthesis import GenerateRemoteSynthesisMakefile


class Default(Action):
    def run(self):
        self._check_manifest()
        tm = self.top_module

        if not self.modules_pool.is_everything_fetched():
            self.fetch(unfetched_only=True)

        if tm.action == "simulation":
            simulation_makefile = SimulationMakefile(modules_pool=self.modules_pool, options=self.options, env=self.env)
            simulation_makefile.run()

        elif tm.action == "synthesis":

            if tm.target == "xilinx":
                ise_project = ISEProject(modules_pool=self.modules_pool, options=self.options, env=self.env)
                ise_project.run()

                ise_makefile = ISEProject(modules_pool=self.modules_pool, options=self.options, env=self.env)
                ise_makefile.run()

                remote_synthesis = ISEProject(modules_pool=self.modules_pool, options=self.options, env=self.env)
                remote_synthesis.run()
            elif tm.target == "altera":
                quartus_project = QuartusProject(modules_pool=self.modules_pool, options=self.options, env=self.env)
                quartus_project.run()
            else:
                logging.error("Unrecognized target: %s" % tm.target)
                sys.exit("Exiting")

    def _check_manifest(self):
        if self.top_module.action != "simulation" and self.top_module.action != "synthesis":
            logging.error("'action' variable must be defined in the top manifest\n"
                          "Allowed values are: \"simulation\" or \"synthesis\"\n"
                          "This variable in a manifest file is necessary for Hdlmake\n"
                          "to be able to know what to do with the given modules' structure.\n"
                          "For more help type `hdlmake --help'\n"
                          "or visit http://www.ohwr.org/projects/hdl-make")
            sys.exit("Exiting")

        if self.top_module.syn_project is None:
            logging.error("syn_project variable must be defined in the manifest")
            sys.exit("Exiting")
