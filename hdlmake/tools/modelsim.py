#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Modified to allow ISim simulation by Lucas Russo (lucas.russo@lnls.br)
# Modified to allow ISim simulation by Adrian Byszuk (adrian.byszuk@lnls.br)
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

from __future__ import print_function
import xml.dom.minidom
import xml.parsers.expat
import os
import re

XmlImpl = xml.dom.minidom.getDOMImplementation()

MODELSIM_STANDARD_LIBS = ['ieee', 'std']


def detect_modelsim_version(path):
    pass



class ModelsiminiReader(object):
    def __init__(self, path=None):
        if path is None:
            path = self.modelsim_ini_dir() + "/modelsim.ini"
        self.path = path

    def get_libraries(self):
        new_section = "\[[^\[\]]+\]"
        libs = []

        try:
            ini = open(self.path, "r")
        except Exception:
            return []

        #p.info("Reading 'modelsim.ini' located in: '"+ str(self.path))

        reading_libraries = False
        for line in ini:
            line = line.split(" ")[0]
            line = line.strip()
            if line == "":
                continue
            if line.lower() == "[library]":
                reading_libraries = True
                continue
            if re.search(new_section, line):
                if reading_libraries is True:
                #reading_libraries = False
                    break
                else:
                    continue
            if reading_libraries:
                line = line.split('=')
                lib = line[0].strip()
                libs.append(lib.lower())
        return libs

    @staticmethod
    def modelsim_ini_dir():
        vsim_path = os.popen("which vsim").read().strip()
        bin_path = os.path.dirname(vsim_path)
        return os.path.abspath(bin_path+"/../")
