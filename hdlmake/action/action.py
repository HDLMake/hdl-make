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

from hdlmake.action import (ActionCheck, ActionCore,
                    ActionTree, ActionSimulation,
                    ActionSynthesis,
                    QsysHwTclUpdate)

class Action(ActionCheck, ActionCore,
             ActionTree, ActionSimulation,
             ActionSynthesis,
             QsysHwTclUpdate):

    def _check_all_fetched_or_quit(self):
        if not self.is_everything_fetched():
            logging.error("At least one module remains unfetched. "
                          "Fetching must be done before makefile generation.")
            print("\nUnfetched modules:")
            print('\n'.join([str(m) for m in self if not m.isfetched]))
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
