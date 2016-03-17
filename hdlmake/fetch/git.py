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
from tempfile import TemporaryFile
from subprocess import Popen, PIPE
from .constants import (GIT, GITSUBMODULE)
from .fetcher import Fetcher
import global_mod


class GitSubmodule(Fetcher):
    def fetch(self, module):
        if module.source != GITSUBMODULE:
            raise ValueError("This backend should get git modules only.")
        cur_dir = global_mod.current_path
        os.chdir(module.fetchto)
        os.system("git submodule init")
        os.system("git submodule update")
        os.chdir(cur_dir)


class Git(Fetcher):
    def __init__(self):
        pass

    @staticmethod
    def get_git_toplevel(module):
        cur_dir = global_mod.current_path
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

    @staticmethod
    def get_git_submodules(module):
        submodule_dir = path.rel2abs(module.path)
        logging.debug("Checking git submodules in %s" % submodule_dir)
        cur_dir = global_mod.current_path
        try:
            os.chdir(submodule_dir)

            if not os.path.exists(".gitmodules"):
                return {}
            #"git config --list" | grep submodule | sed 's/.*=//')" % submodule_dir
            config_submodules = {}
            config_content = Popen("git config -f .gitmodules --list",
                                      stdout=PIPE,
                                      stdin=PIPE,
                                      shell=True)
            config_lines = [line.strip() for line in config_content.stdout.readlines()]
            """try to parse sth like this:
paszoste@oplarra1:~/beco/hdlmake-tests/wr-switch-hdl$ git config -f .gitmodules --list
submodule.ip_cores/general-cores.path=ip_cores/general-cores
submodule.ip_cores/general-cores.url=git://ohwr.org/hdl-core-lib/general-cores.git
submodule.ip_cores/wr-cores.path=ip_cores/wr-cores
submodule.ip_cores/wr-cores.url=git://ohwr.org/hdl-core-lib/wr-cores.git
"""
            config_submodule_lines = [line for line in config_lines if line.startswith("submodule")]
            for line in config_submodule_lines:
                line_split = line.split("=")
                lhs = line_split[0]
                rhs = line_split[1]
                lhs_split = lhs.split(".")
                module_name = '.'.join(lhs_split[1:-1])
                if module_name not in config_submodules:
                    config_submodules[module_name] = {}
                config_submodules[module_name][lhs_split[-1]] = rhs


            #"(cd %s && cat ./.gitmodules 2>/dev/null | grep url | sed 's/url = //')" % submodule_dir
            #try:
            ##    dotgitmodules_file = open(".gitmodules", 'r')
             #   dotgitmodules_lines = dotgitmodules_file.readlines()
             #   url_lines = [line for line in dotgitmodules_lines if 'url' in line]
             #   dotgitmodules_submodules = [line.split(" = ")[-1].strip() for line in url_lines]

             #  set(config_submodules).update(set(dotgitmodules_submodules))
            #except IOError:
             #   pass  # no .gitmodules file
            if len(list(config_submodules)) > 0:
                logging.info("Found git submodules in %s: %s" % (module.path, str(config_submodules)))
        finally:
            os.chdir(cur_dir)
        return config_submodules

    def fetch(self, module):
        if module.source != GIT:
            raise ValueError("This backend should get git modules only.")
        if not os.path.exists(module.fetchto):
            os.mkdir(module.fetchto)

        cur_dir = global_mod.current_path
        if module.branch is None:
            module.branch = "master"

        basename = path.url_basename(module.url)
        mod_path = os.path.join(module.fetchto, basename)

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
            cmd = cmd.format(module.fetchto, module.url, module.branch)

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
        cur_dir = global_mod.current_path
        commit = None
        stderr = TemporaryFile()
        try:
            os.chdir(path)
            git_cmd = 'git log -1 --format="%H" | cut -c1-32'
            git_out = Popen(git_cmd,
                            shell=True,
                            stdin=PIPE,
                            stdout=PIPE,
                            stderr=stderr,
                            close_fds=True)
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
