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

from action import Action
from util import path
import fetch


class ListModules(Action):
    def run(self):
        if self.options.withfiles:
            for m in self.modules_pool:
                if not m.isfetched:
                    print("#!UNFETCHED")
                    print(m.url+'\n')
                else:
                    print(path.relpath(m.path))
                    if m.source in [fetch.SVN, fetch.GIT]:
                        print("# "+m.url)
                    if m.parent:
                        print("# defined in %s" % m.parent.url)
                    else:
                        print("# root module")
                    if not len(m.files):
                        print("   # no files")
                    else:
                        for f in m.files:
                            print("   " + path.relpath(f.path, m.path))
                    print("")
        else:
            print("#path\tsource")
            for m in self.modules_pool:
                print("%s\t%s" % (path.relpath(m.path), m.source))
