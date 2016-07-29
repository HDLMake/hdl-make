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

import sys
import logging
import importlib

class Action(object):
    def __init__(self, modules_pool):
        self.modules_pool = modules_pool
        self.options = modules_pool.env.options
        self.env = modules_pool.env

        if modules_pool.get_top_module().manifest_dict["action"] is "synthesis":
            tool_name = modules_pool.get_top_module().manifest_dict["syn_tool"]
        elif modules_pool.get_top_module().manifest_dict["action"] is "simulation":
            tool_name = modules_pool.get_top_module().manifest_dict["sim_tool"]
        tool_module = self._load_tool(tool_name)
        self.tool = tool_module.ToolControls()
        self._check_manifest()
        self._check_env()
        self._check_options()

    @property
    def top_module(self):
        return self.modules_pool.get_top_module()

    def _check_manifest(self):
        pass

    def _check_env(self):
        pass

    def _check_options(self):
        pass

    def run(self):
        raise NotImplementedError()

    def _load_tool(self, tool_name):
        try:
            tool_module = importlib.import_module("hdlmake.tools.%s.%s" % (tool_name, tool_name))
        except Exception as e:
            logging.error(e)
            quit()
        return tool_module


    def _check_all_fetched_or_quit(self):
        pool = self.modules_pool
        if not pool.is_everything_fetched():
            logging.error("At least one module remains unfetched. "
                          "Fetching must be done before makefile generation.")
            print("\nUnfetched modules:")
            print('\n'.join([str(m) for m in self.modules_pool if not m.isfetched]))
            sys.exit("\nExiting.")

    def _check_manifest_variable_is_set(self, name):
        if getattr(self.top_module, name) is None:
            logging.error("Variable %s must be set in the manifest to perform current action (%s)"
                          % (name, self.__class__.__name__))
            sys.exit("\nExiting")

    def _check_manifest_variable_is_equal_to(self, name, value):
        ok = False
        try:
            manifest_value = getattr(self.top_module, name)
            if manifest_value == value:
                ok = True
        except:
            pass

        if ok is False:
            logging.error("Variable %s must be set in the manifest and equal to '%s'." % (name, value))
            sys.exit("Exiting")
