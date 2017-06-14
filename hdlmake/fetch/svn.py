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

"""Module providing the stuff for handling SVN repositories"""

from __future__ import absolute_import
import os
import logging
from hdlmake.util import path as path_utils
from .fetcher import Fetcher


class Svn(Fetcher):

    """This class provides the SVN fetcher instances, that are
    used to fetch and handle SVN repositories"""

    def __init__(self):
        pass

    def fetch(self, module):
        """Get the code from the remote SVN repository"""
        fetchto = module.fetchto()
        if not os.path.exists(fetchto):
            os.mkdir(fetchto)
        basename = path_utils.svn_basename(module.url)
        mod_path = os.path.join(fetchto, basename)
        cmd = "cd {0} && svn checkout {1} " + basename
        if module.revision:
            cmd = cmd.format(fetchto, module.url + '@' + module.revision)
        else:
            cmd = cmd.format(fetchto, module.url)
        success = True
        logging.info("Checking out module %s", mod_path)
        logging.debug(cmd)
        if os.system(cmd) != 0:
            success = False
        module.isfetched = True
        module.path = mod_path
        return success

    @staticmethod
    def check_svn_revision(path):
        """Get the revision number for the SVN repository at path"""
        svn_cmd = "svn info 2>/dev/null | awk '{if(NR == 5) {print $2}}'"
        return Fetcher.check_id(path, svn_cmd)
