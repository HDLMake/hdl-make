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

from __future__ import print_function
import logging
import sys
import importlib

from hdlmake.dep_file import DepFile
import hdlmake.new_dep_solver as dep_solver
from hdlmake.srcfile import SourceFileFactory, SourceFileSet
from hdlmake.dependable_file import DependableFile

from .action import Action

class GenerateSimulationMakefile(Action):

    def _check_manifest(self):
        if not self.modules_pool.get_top_module().top_module:
            logging.error("top_module variable must be set in the top manifest.")
            sys.exit("Exiting")
        if not self.modules_pool.get_top_module().sim_tool:
            logging.error("sim_tool variable must be set in the top manifest.")
            sys.exit("Exiting")


    def run(self):
        self._check_all_fetched_or_quit()
        self._check_manifest()
        tool_name = self.modules_pool.get_top_module().sim_tool
        try:
            tool_module = importlib.import_module("hdlmake.tools.%s.%s" % (tool_name, tool_name))
        except Exception as e:
            logging.error(e)
            quit()
        tool_object = tool_module.ToolControls()
        self._generate_simulation_makefile(tool_object)


    def _generate_simulation_makefile(self, tool_object):

        tool_info = tool_object.get_keys()
        if sys.platform == 'cygwin':
            bin_name = tool_info['windows_bin']
        else:
            bin_name = tool_info['linux_bin']

        path_key = tool_info['id'] + '_path'
        version_key = tool_info['id'] + '_version'
        name = tool_info['name']

        self.env.check_tool(tool_object)
        self.env.check_general()

        if self.env[path_key] is None and self.options.force is not True:
            logging.error("Can't generate a " + name + " makefile. " + bin_name + " not found.")
            sys.exit("Exiting")
            
        logging.info("Generating " + name + " makefile for simulation.")

        self.modules_pool.build_file_set()
        tool_object.generate_simulation_makefile(
            self.modules_pool.hierarchy_solved, 
            self.modules_pool.get_top_module()
        )

