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

from .action import Action


class CheckManifest(Action):
    def _check_options(self):
        if not self.options.top:
            logging.info("--top is not specified. Current manifest will be treated as the top manifest")

    def run(self):
        ###
        ### THIS IS JUST A STUB
        ###
        pass
        #manifest_parser = ManifestParser()

        #manifest_parser.add_arbitrary_code("__manifest=\""+self.path+"\"")
        #manifest_parser.add_arbitrary_code(global_mod.options.arbitrary_code)

        #opt_map = manifest_parser.parse()
