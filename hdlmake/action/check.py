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
import logging
import sys
import re

from .action import Action


class ActionCheck(Action):

    def check_manifest(self):
        logging.error("This action is not implemented yet!")


    def check_condition(self):

        def _compare(local, reference, cond):
            if cond == "==":
                return local == reference
            elif cond == "<":
                return local < reference
            elif cond == ">":
                return local > reference
            elif cond == "<=":
                return local <= reference
            elif cond == ">=":
                return local >= reference
            else:
                sys.exit(1)

        tool = self.env.options.tool
        if tool == "ise":
            ver = self.env["ise_version"]
            if not ver:
                sys.exit(1)
            ref = self.env.options.reference
            ver = float(ver)
            ref = float(ref)
        elif tool == "quartus":
            ver = self.env["quartus_version"]
            if not ver:
                sys.exit(1)
            ref = self.env.options.reference
        elif tool == "modelsim":
            ver = self.env["modelsim_version"]
            if not ver:
                sys.exit(1)
            ref = self.env.options.reference
        elif tool == "iverilog":
            ver = self.env["iverilog_version"]
            if not ver:
                sys.exit(1)
            ref = self.env.options.reference
            ver = int(ver.replace('.', ''))
            ref = int(ref.replace('.', ''))
        elif tool == "isim":
            ver = self.env["ise_version"]
            if not ver:
                sys.exit(1)
            ref = self.env.options.reference
            ver = re.sub("[a-zA-Z]", '', ver)
            ref = re.sub("[a-zA-Z]", '', ref)
        else:
            logging.error("Unknown tool: %s" % tool)
            sys.exit("\nExiting")

        comparison = _compare(ver, ref, self.env.options.condition)
        sys.exit(int(not comparison))
