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
from hdlmake.util import path
import logging
import platform
from tempfile import TemporaryFile
from subprocess import Popen, PIPE
from .constants import GIT
from .fetcher import Fetcher


class Git(Fetcher):
    def __init__(self):
        pass

    @staticmethod
    def get_git_toplevel(module):
        cur_dir = module.pool.top_module.path
        try:
            os.chdir(path.rel2abs(module.path))
            if not os.path.exists(".gitmodules"):
                return None
            tree_root_cmd = Popen("git rev-parse --show-toplevel",
                              stdout=PIPE,
                              stdin=PIPE,
                              shell=True)
            tree_root_line = tree_root_cmd.stdout.readlines()[0].strip()
            return tree_root_line
        finally:
            os.chdir(cur_dir)


    def fetch(self, module):
        fetchto = module.fetchto()
        if module.source != GIT:
            raise ValueError("This backend should get git modules only.")
        if not os.path.exists(fetchto):
            os.mkdir(fetchto)

        cur_dir = module.pool.top_module.path
        if module.branch is None:
            module.branch = "master"

        basename = path.url_basename(module.url)
        mod_path = os.path.join(fetchto, basename)

        logging.info("Fetching git module: %s" % mod_path)

        if basename.endswith(".git"):
            basename = basename[:-4]  # remove trailing .git

        if module.isfetched:
            update_only = True
        else:
            update_only = False

        if update_only:
            logging.info("Updating module %s" % mod_path)
            cmd = "(cd {0} && git checkout {1})"
            cmd = cmd.format(mod_path, module.branch)
        else:
            logging.info("Cloning module %s" % mod_path)
            cmd = "(cd {0} && git clone -b {2} {1})"
            cmd = cmd.format(fetchto, module.url, module.branch)

        success = True

        logging.debug("Running %s" % cmd)
        if os.system(cmd) != 0:
            success = False

        if module.revision is not None and success is True:
            logging.debug("cd %s" % mod_path)
            os.chdir(mod_path)
            cmd = "git checkout " + module.revision
            logging.debug("Running %s" % cmd)
            if os.system(cmd) != 0:
                success = False
            os.chdir(cur_dir)

        module.isfetched = True
        module.path = mod_path
        return success

    @staticmethod
    def check_commit_id(path):
        cur_dir = os.getcwd()
        commit = None
        stderr = TemporaryFile()
        try:
            is_windows = path.check_windows()
            os.chdir(path)
            git_cmd = 'git log -1 --format="%H" | cut -c1-32'
            git_out = Popen(git_cmd,
                            shell=True,
                            stdin=PIPE,
                            stdout=PIPE,
                            stderr=stderr,
                            close_fds=not is_windows)
            errmsg = stderr.readlines()
            if errmsg:
                logging.debug("git error message (in %s): %s" % (path, '\n'.join(errmsg)))

            try:
                commit = git_out.stdout.readlines()[0].strip()
            except IndexError:
                pass
        finally:
            os.chdir(cur_dir)
            stderr.close()
        return commit
