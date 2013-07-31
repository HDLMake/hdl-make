# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Modified to allow ISim simulation by Lucas Russo (lucas.russo@lnls.br)
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
#

import logging


class DependableFile:
    def __init__(self):
        self.dep_index = None
        self.dep_resolved = False
        self.__dep_provides = None
        self.__dep_requires = None
        self.__dep_depends_on = []

    #use proxy template here
    def __get_dep_provides(self):
        if self.__dep_provides is None:
            self._create_deps_provides()
        assert self.__dep_provides is not None
        return self.__dep_provides

    def __set_dep_provides(self, what):
        self.__dep_provides = what

    dep_provides = property(__get_dep_provides, __set_dep_provides)

    def __get_dep_requires(self):
        if self.__dep_requires is None:
            self._create_deps_requires()
        assert self.__dep_requires is not None
        return self.__dep_requires

    def __set_dep_requires(self, what):
        self.__dep_requires = what

    dep_requires = property(__get_dep_requires, __set_dep_requires)

    def __get_dep_depends_on(self):
        return self.__dep_depends_on

    def __set_dep_depends_on(self, what):
        self.__dep_depends_on = what
    dep_depends_on = property(__get_dep_depends_on, __set_dep_depends_on)

    def _create_deps_requires(self):
        logging.error(str(type(self)) + " " + self.path)

    def _create_deps_provides(self):
        logging.error(str(type(self)) + " " + self.path)
