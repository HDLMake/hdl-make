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
import sys
from action import Action


class FetchModules(Action):
    def _check_options(self):
        if self.options.flatten is True and self.env["coredir"] is not None:
            logging.error("Options clash: --flatten and HDLMAKE_COREDIR set at a time\n"
                          "Take one out of the two")
            sys.exit("\nExiting")

    def run(self):
        logging.info("Fetching needed modules.")
        self.modules_pool.fetch_all(unfetched_only=not self.options.update, flatten=self.options.flatten)
        logging.debug(str(self.modules_pool))
        logging.info("All modules fetched.")