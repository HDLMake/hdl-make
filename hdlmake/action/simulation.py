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
from action import Action
import logging
import sys
import global_mod


class GenerateSimulationMakefile(Action):
    def _check_manifest(self):
        if not self.modules_pool.get_top_module().top_module:
            logging.error("top_module variable must be set in the top manifest.")
            sys.exit("Exiting")

    def run(self):
        self._check_all_fetched_or_quit()
        self._check_manifest()

        tm = self.modules_pool.top_module
        if tm.sim_tool == "iverilog":
            self._generate_iverilog_makefile()
        elif tm.sim_tool == "isim":
            self._generate_isim_makefile()
        elif tm.sim_tool == "vsim" or tm.sim_tool == "modelsim":
            self._generate_vsim_makefile()
        else:
            logging.error("Unrecognized or not specified simulation tool: %s" % str(tm.sim_tool))
            sys.exit("Exiting")

    def _generate_vsim_makefile(self):
        if self.env["modelsim_path"] is None:
            logging.error("Can't generate a Modelsim makefile. Modelsim not found.")
            sys.exit("Exiting")

        from dep_file import DepFile
        logging.info("Generating ModelSim makefile for simulation.")

        pool = self.modules_pool
        top_module = pool.get_top_module()
        fset = pool.build_file_set()
        dep_files = fset.filter(DepFile)
        global_mod.makefile_writer.generate_vsim_makefile(dep_files, top_module)

    def _generate_isim_makefile(self):
        if self.env["isim_path"] is None and self.env["xilinx"] is None:
            logging.error("Can't generate an ISim makefile. ISim not found.")
            sys.exit("Exiting")

        logging.info("Generating ISE Simulation (ISim) makefile for simulation.")

        pool = self.modules_pool
        top_module = pool.get_top_module()

        fset = pool.build_file_set()
        global_mod.makefile_writer.generate_isim_makefile(fset, top_module)

    def _generate_iverilog_makefile(self):
        logging.info("Generating IVerilog makefile for simulation.")
        if self.env["iverilog_path"] is None:
            logging.error("Can't generate an IVerilog makefile. IVerilog not found.")
            sys.exit("Exiting")

        pool = self.modules_pool

        tm = pool.get_top_module()
        fset = pool.build_file_set()
        global_mod.makefile_writer.generate_iverilog_makefile(fset, tm, pool)
