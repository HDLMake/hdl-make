#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013, 2014 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Multi-tool support by Javier D. Garcia-Lasheras (javier@garcialasheras.com)
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

"""This module provides the simulation wrapper for HDLMake"""

from __future__ import print_function
import logging
import sys

from hdlmake.dep_file import DepFile
# import hdlmake.new_dep_solver as dep_solver

from hdlmake.tools import WriterSim

from .action import Action

class ActionSimulation(Action):

    """This class contains the simulation specific methods"""

    def __init__(self, *args):
        self.sim_writer = WriterSim()
        super(ActionSimulation, self).__init__(*args)

    def _check_simulation_makefile(self):
        """Check if the simulation keys are provided by the top manifest"""
        if not self.get_top_module().manifest_dict["sim_top"]:
            logging.error("sim_top variable must be set in the top manifest.")
            sys.exit("Exiting")
        if not self.get_top_module().manifest_dict["sim_tool"]:
            logging.error("sim_tool variable must be set in the top manifest.")
            sys.exit("Exiting")

    def simulation_makefile(self):
        """Execute the simulation action"""
        self._check_all_fetched_or_quit()
        self._check_simulation_makefile()
        tool_name = self.get_top_module().manifest_dict["sim_tool"]
        tool_dict = {"iverilog": self.sim_writer.iverilog,
                     "isim": self.sim_writer.isim,
                     "modelsim": self.sim_writer.modelsim,
                     "active-hdl": self.sim_writer.active_hdl,
                     "riviera":  self.sim_writer.riviera,
                     "ghdl": self.sim_writer.ghdl}
        if not tool_name in tool_dict:
            logging.error("Unknown sim_tool: %s", tool_name)
            sys.exit("Exiting")
        tool_object = tool_dict[tool_name]
        tool_info = tool_object.TOOL_INFO
        if sys.platform == 'cygwin':
            bin_name = tool_info['windows_bin']
        else:
            bin_name = tool_info['linux_bin']
        path_key = tool_info['id'] + '_path'
        name = tool_info['name']
        self.env.check_tool(tool_object)
        self.env.check_general()
        if self.env[path_key] is None and self.env.options.force is not True:
            logging.error("Can't generate a " + name + " makefile. " +
                          bin_name + " not found.")
            sys.exit("Exiting")
        logging.info("Generating " + name + " makefile for simulation.")
        top_module = self.get_top_module()
        fset = self.build_file_set(top_module.manifest_dict["sim_top"])
        dep_files = fset.filter(DepFile)
        # dep_solver.solve(dep_files)
        # tool_object.generate_simulation_makefile(dep_files, top_module)
        tool_object.makefile_setup(top_module, dep_files)
        tool_object.makefile_sim_top()
        tool_object.makefile_sim_options()
        tool_object.makefile_sim_local()
        tool_object.makefile_sim_sources()
        tool_object.makefile_sim_compilation()
        tool_object.makefile_sim_command()
        tool_object.makefile_sim_clean()
        tool_object.makefile_sim_phony()
