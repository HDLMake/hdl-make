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

"""This module provides the synthesis functionality to HDLMake"""

from __future__ import print_function
import logging
import sys

from hdlmake.tools import WriterSyn

from .action import Action


class ActionSynthesis(Action):

    """Class providing the public synthesis methods for the user"""

    def __init__(self, *args):
        self.syn_writer = WriterSyn()
        super(ActionSynthesis, self).__init__(*args)

    def _load_synthesis_tool(self):
        """Returns a tool_object that provides the synthesis tool interface"""
        tool_name = self.get_top_module().manifest_dict["syn_tool"]
        tool_dict = {"ise": self.syn_writer.ise,
                     "planahead": self.syn_writer.planahead,
                     "vivado": self.syn_writer.vivado,
                     "quartus": self.syn_writer.quartus,
                     "diamond": self.syn_writer.diamond,
                     "libero": self.syn_writer.libero}
        if not tool_name in tool_dict:
            logging.error("Synthesis tool not recognized: %s", tool_name)
            quit()
        return tool_dict[tool_name]

    def _check_synthesis_project(self):
        """Check the manifest contains all the keys for a synthesis project"""
        manifest = self.get_top_module().manifest_dict
        if not manifest["syn_tool"]:
            logging.error(
                "syn_tool variable must be set in the top manifest.")
            sys.exit("Exiting")
        if not manifest["syn_device"]:
            logging.error(
                "syn_device variable must be set in the top manifest.")
            sys.exit("Exiting")
        if not manifest["syn_grade"]:
            logging.error(
                "syn_grade variable must be set in the top manifest.")
            sys.exit("Exiting")
        if not manifest["syn_package"]:
            logging.error(
                "syn_package variable must be set in the top manifest.")
            sys.exit("Exiting")
        if not manifest["syn_top"]:
            logging.error(
                "syn_top variable must be set in the top manifest.")
            sys.exit("Exiting")

    def synthesis_project(self):
        """Generate a project for the specific synthesis tool"""
        self._check_all_fetched_or_quit()
        self._check_synthesis_project()
        tool_object = self._load_synthesis_tool()
        tool_info = tool_object.TOOL_INFO
        path_key = tool_info['id'] + '_path'
        name = tool_info['name']
        env = self.env
        env.check_tool(tool_object)
        top_module = self.get_top_module()
        if env[path_key]:
            tool_path = env[path_key]
        else:
            tool_path = ""
        top_mod = self.get_top_module()
        fileset = self.build_file_set(top_mod.manifest_dict["syn_top"],
                                      standard_libs=tool_object.STANDARD_LIBS)
        sup_files = self.build_complete_file_set()
        privative_files = []
        for file_aux in sup_files:
            if any(isinstance(file_aux, file_type)
                   for file_type in tool_object.SUPPORTED_FILES):
                privative_files.append(file_aux)
        if len(privative_files) > 0:
            logging.info("Detected %d supported files that are not parseable",
                         len(privative_files))
            fileset.add(privative_files)
        tool_object.makefile_setup(top_module, fileset)
        tool_object.makefile_includes()
        tool_object.makefile_syn_top(tool_path)
        tool_object.makefile_syn_tcl()
        tool_object.makefile_syn_files()
        tool_object.makefile_syn_local()
        tool_object.makefile_syn_command()
        tool_object.makefile_syn_build()
        tool_object.makefile_syn_clean()
        tool_object.makefile_syn_phony()
        logging.info(name + " project file generated.")
