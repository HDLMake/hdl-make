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

from .action import Action

class GenerateSynthesisMakefile(Action):

    def _check_manifest(self):
        # NOTE: top_module is not used in synthesis!!
        if not self.modules_pool.get_top_module().manifest_dict["syn_top"]:
            logging.error("syn_top variable must be set in the top manifest.")
            sys.exit("Exiting")
        if not self.modules_pool.get_top_module().manifest_dict["syn_tool"]:
            logging.error("syn_tool variable must be set in the top manifest.")
            sys.exit("Exiting")


    def run(self):
        self._check_all_fetched_or_quit()
        self._check_manifest()
        self._generate_synthesis_makefile()


    def _generate_synthesis_makefile(self):
        tool_object = self.tool 

        tool_info = tool_object.get_keys()
        if sys.platform == 'cygwin':
            bin_name = tool_info['windows_bin']
        else:
            bin_name = tool_info['linux_bin']
        path_key = tool_info['id'] + '_path'
        version_key = tool_info['id'] + '_version'
        name = tool_info['name']

        env = self.env
        env.check_general()
        env.check_tool(tool_object)

        if env[path_key]:
            tool_path = env[path_key]
        else:
            tool_path = ""
        
        logging.info("Generating synthesis makefile for " + name)
        tool_object.generate_synthesis_makefile(top_mod=self.modules_pool.get_top_module(),
                                                         tool_path=tool_path)
        logging.info("Synthesis makefile generated.")

