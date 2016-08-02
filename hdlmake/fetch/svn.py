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

import os
import logging
import platform
from tempfile import TemporaryFile
from subprocess import Popen, PIPE
from hdlmake.util import path
from .fetcher import Fetcher


class Svn(Fetcher):
    def __init__(self):
        pass

    def fetch(self, module):

        fetchto = module.fetchto()
        if not os.path.exists(fetchto):
            os.mkdir(fetchto)

        cur_dir = module.pool.top_module.path
        os.chdir(fetchto)

        basename = path.svn_basename(module.url)
        mod_path = os.path.join(fetchto, basename)

        cmd = "svn checkout {0} " + module.basename
        if module.revision:
            cmd = cmd.format(module.url + '@' + module.revision)
        else:
            cmd = cmd.format(module.url)

        success = True

        logging.info("Checking out module %s" % mod_path)
        logging.debug(cmd)
        if os.system(cmd) != 0:
            success = False
        os.chdir(cur_dir)

        module.isfetched = True
        module.path = os.path.join(fetchto, module.basename)
        return success

    @staticmethod
    def check_revision_number(path):
        cur_dir = os.getcwd()
        revision = None
        stderr = TemporaryFile()

        try:
            is_windows = path.check_windows()
            os.chdir(path)
            svn_cmd = "svn info 2>/dev/null | awk '{if(NR == 5) {print $2}}'"
            svn_out = Popen(svn_cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=stderr, close_fds=not is_windows)
            errmsg = stderr.readlines()
            if errmsg:
                logging.debug("svn error message (in %s): %s" % (path, '\n'.join(errmsg)))

            try:
                revision = svn_out.stdout.readlines()[0].strip()
            except IndexError:
                pass
        finally:
            os.chdir(cur_dir)
            stderr.close()
        return revision
