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
import hdlmake.new_dep_solver as dep_solver
from hdlmake.util import path as path_mod


class ActionCore(Action):

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


    def list_files(self):
        unfetched_modules = [m for m in self if not m.isfetched]
        for m in unfetched_modules:
            logging.warning("List incomplete, module %s has not been fetched!", m)
        file_set = self.build_file_set()
        file_list = dep_solver.make_dependency_sorted_list(file_set)
        files_str = [f.path for f in file_list]
        if self.env.options.delimiter == None:
            delimiter = "\n"
        else:
            delimiter = self.env.options.delimiter
        print(delimiter.join(files_str))


    def list_modules(self):

        def _convert_to_source_name(source_code):
            if source_code == fetch.GIT:
                return "git"
            elif source_code == fetch.SVN:
                return "svn"
            elif source_code == fetch.LOCAL:
                return "local"
            elif source_code == fetch.GITSUBMODULE:
                return "git_submodule"

        terse = self.env.options.terse
        for m in self:
            if not m.isfetched:
                logging.warning("Module not fetched: %s" % m.url)
                if not terse: print("# MODULE UNFETCHED! -> %s" % m.url)
            else:
                if not terse: print("# MODULE START -> %s" % m.url)
                if m.source in [fetch.SVN, fetch.GIT]:
                    if not terse: print("# * URL: "+m.url)
                if m.source in [fetch.SVN, fetch.GIT, fetch.LOCAL] and m.parent:
                    if not terse: print("# * The parent for this module is: %s" % m.parent.url)
                else:
                    if not terse: print("# * This is the root module")
                print("%s\t%s" % (path_mod.relpath(m.path), _convert_to_source_name(m.source)))
                if self.env.options.withfiles:
                    if not len(m.files):
                        if not terse: print("# * This module has no files")
                    else:
                        for f in m.files:
                            print("%s\t%s" % (path_mod.relpath(f.path), "file"))
                if not terse: print("# MODULE END -> %s" % m.url)
            if not terse: print("")


