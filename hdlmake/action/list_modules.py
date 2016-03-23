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

from __future__ import absolute_import

import logging

from hdlmake.util import path
import hdlmake.fetch as fetch

from .action import Action


def _convert_to_source_name(source_code):
    if source_code == fetch.GIT:
        return "git"
    elif source_code == fetch.SVN:
        return "svn"
    elif source_code == fetch.LOCAL:
        return "local"
    elif source_code == fetch.GITSUBMODULE:
        return "git_submodule"


class ListModules(Action):
    def run(self):
        for m in self.modules_pool:
            if not m.isfetched:
                logging.warning("Module not fetched: %s" % m.url)
                if not self.options.terse: print("# MODULE UNFETCHED! -> %s" % m.url)
            else:
                if not self.options.terse: print("# MODULE START -> %s" % m.url)
                if m.source in [fetch.SVN, fetch.GIT]:
                    if not self.options.terse: print("# * URL: "+m.url)
                elif m.source == fetch.GITSUBMODULE:
                    if not self.options.terse: print("# * This is a submodule of: %s" % m.parent.url)
                if m.source in [fetch.SVN, fetch.GIT, fetch.LOCAL] and m.parent:
                    if not self.options.terse: print("# * The parent for this module is: %s" % m.parent.url)
                else:
                    if not self.options.terse: print("# * This is the root module")
                print("%s\t%s" % (path.relpath(m.path), _convert_to_source_name(m.source)))
                if self.options.withfiles:
                    if not len(m.files):
                        if not self.options.terse: print("# * This module has no files")
                    else:
                        for f in m.files:
                            print("%s\t%s" % (path.relpath(f.path), "file"))
                if not self.options.terse: print("# MODULE END -> %s" % m.url)
            if not self.options.terse: print("")

