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

"""Module providing the stuff for handling Git repositories"""

from __future__ import absolute_import
import os
from hdlmake.util import path as path_utils
from hdlmake.util import shell
import logging
from .fetcher import Fetcher


class Git(Fetcher):

    """This class provides the Git fetcher instances, that are
    used to fetch and handle Git repositories"""

    def __init__(self):
        pass

    @staticmethod
    def get_git_toplevel():
        """Get the top level for the Git repository"""
        return shell.run("git rev-parse --show-toplevel")

    @staticmethod
    def get_submodule_commit(submodule_dir):
        """Get the commit for a repository if defined in Git submodules"""
        status_line = shell.run("git submodule status %s" % submodule_dir)
        status_line = status_line.split()
        if len(status_line) == 2:
            return status_line[0][1:]
        else:
            return None

    def fetch(self, module):
        """Get the code from the remote Git repository"""
        fetchto = module.fetchto()
        if not os.path.exists(fetchto):
            os.mkdir(fetchto)
        basename = path_utils.url_basename(module.url)
        mod_path = os.path.join(fetchto, basename)
        if basename.endswith(".git"):
            basename = basename[:-4]  # remove trailing .git
        if not module.isfetched:
            logging.info("Fetching git module %s", mod_path)
            cmd = "(cd {0} && git clone {1})"
            cmd = cmd.format(fetchto, module.url)
            if os.system(cmd) != 0:
                return False
        else:
            logging.info("Updating git module %s", mod_path)
        checkout_id = None
        if module.branch is not None:
            checkout_id = module.branch
            logging.debug("Git branch requested: %s", checkout_id)
        elif module.revision is not None:
            checkout_id = module.revision
            logging.debug("Git commit requested: %s", checkout_id)
        else:
            checkout_id = self.get_submodule_commit(module.path)
            logging.debug("Git submodule commit: %s", checkout_id)
        if checkout_id is not None:
            logging.info("Checking out version %s", checkout_id)
            cmd = "(cd {0} && git checkout {1})"
            cmd = cmd.format(mod_path, checkout_id)
            if os.system(cmd) != 0:
                return False
        module.isfetched = True
        module.path = mod_path
        return True

    @staticmethod
    def check_git_commit(path):
        """Get the revision number for the Git repository at path"""
        git_cmd = 'git log -1 --format="%H" | cut -c1-32'
        return Fetcher.check_id(path, git_cmd)
