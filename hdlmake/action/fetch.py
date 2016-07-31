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
import hdlmake.fetch as fetch


class FetchModules(Action):

    def fetch(self):
        top_module = self.get_top_module()
        logging.info("Fetching needed modules.")
        os.system(top_module.manifest_dict["fetch_pre_cmd"])
        self.fetch_all()
        os.system(top_module.manifest_dict["fetch_post_cmd"])
        logging.info("All modules fetched.")


    def clean(self):
        logging.info("Removing fetched modules..")
        remove_list = [m for m in self if m.source in [fetch.GIT, fetch.SVN] and m.isfetched]
        remove_list.reverse()  # we will remove modules in backward order
        if len(remove_list):
            for m in remove_list:
                logging.info("... clean: " + m.url + " [from: " + m.path + "]")
                m.remove_dir_from_disk()
        else:
            logging.info("There are no modules to be removed")
        logging.info("Modules cleaned.")

