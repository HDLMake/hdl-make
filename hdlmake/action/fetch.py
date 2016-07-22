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
import os

from .action import Action


class FetchModules(Action):

    def run(self):
        top_module = self.modules_pool.get_top_module()
        logging.info("Fetching needed modules.")
        os.system(top_module.fetch_pre_cmd)
        self.modules_pool.fetch_all()
        logging.debug(str(self.modules_pool))
        os.system(top_module.fetch_post_cmd)
        logging.info("All modules fetched.")
