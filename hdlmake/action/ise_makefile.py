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
import global_mod


class GenerateISEMakefile(Action):
    def _check_manifest(self):
        self._check_manifest_variable_is_set("syn_tool")

    def run(self):
        logging.info("Generating makefile for local synthesis.")
        if global_mod.env["ise_path"]:
            ise_path = global_mod.env["ise_path"]
        else:
            ise_path = ""

        global_mod.makefile_writer.generate_ise_makefile(top_mod=self.modules_pool.get_top_module(),
                                                         ise_path=ise_path)
        logging.info("Local synthesis makefile generated.")