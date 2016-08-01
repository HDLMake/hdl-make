#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013-2016 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
#         Garcia-Lasheras (javier@garcialasheras.com)
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

"""This is the Python module providing the container for the HDL Modules"""

from __future__ import print_function
import os
import logging
import platform
from subprocess import PIPE, Popen
import sys

from .util import path as path_mod
from . import fetch
from .env import Env

from .action import (ActionCheck, ActionCore,
                    ActionTree, ActionSimulation,
                    ActionSynthesis,
                    QsysHwTclUpdate)


class ModulePool(ActionCheck, ActionCore,
                 ActionTree, ActionSimulation,
                 ActionSynthesis,
                 QsysHwTclUpdate):
    """
    The ModulePool class acts as the container for the HDLMake modules that
    are progressively being added to the design hierarchy.
    """

    def __init__(self, *args):
        ActionCheck.__init__(self, *args)
        ActionCore.__init__(self, *args)
        ActionTree.__init__(self, *args)
        ActionSimulation.__init__(self, *args)
        ActionSynthesis.__init__(self, *args)
        QsysHwTclUpdate.__init__(self, *args)

    def set_environment(self, options):
        """Initialize the module pool environment from the provided options"""
        env = Env(options)
        self.env = env

    def get_module_by_path(self, path):
        """Get instance of Module being stored at a given location"""
        path = path_mod.rel2abs(path)
        for module in self:
            if module.path == path:
                return module
        return None

    def get_fetchable_modules(self):
        """Get list with the remote modules, i.e. those that can be fetched"""
        return [m for m in self if m.source != fetch.LOCAL]

    def __str__(self):
        """Cast the module list as a list of strings"""
        return str([str(m) for m in self])

    def __contains(self, module):
        """Check if the pool contains the given module by checking the URL"""
        for mod in self:
            if mod.url == module.url:
                return True
        return False


    def new_module(self, parent, url, source, fetchto):
        """Add new module to the pool.

        This is the only way to add new modules to the pool
        Thanks to it the pool can easily control its content

        NOTE: the first module added to the pool will become the top_module!.
        """
        from .module import Module, ModuleArgs
        self._deps_solved = False

        new_module_args = ModuleArgs()
        new_module_args.set_args(parent, url, source, fetchto)
        new_module = Module(new_module_args, self)

        if not self.__contains(new_module):
            self._add(new_module)
            if not self.top_module:
                self.top_module = new_module
                new_module.parse_manifest()
                url = self._guess_origin(self.top_module.path)
                if url:
                    self.top_module.url = url

        return new_module


    def _guess_origin(self, path):
        """Guess origin (git, svn, local) of a module at given path"""
        cwd = self.top_module.path
        try:
            if platform.system() == 'Windows':
                is_windows = True
            else:
                is_windows = False
            os.chdir(path)
            git_out = Popen("git config --get remote.origin.url",
                            stdout=PIPE, shell=True, close_fds=not is_windows)
            lines = git_out.stdout.readlines()
            if len(lines) == 0:
                return None
            url = lines[0].strip()
            if not url:  # try svn
                svn_out = Popen(
                    "svn info | grep 'Repository Root' | awk '{print $NF}'",
                    stdout=PIPE, shell=True, close_fds=not is_windows)
                url = svn_out.stdout.readlines()[0].strip()
                if url:
                    return url
                else:
                    return None
            else:
                return url
        finally:
            os.chdir(cwd)

    def _add(self, new_module):
        """Add the given new module if this is not already in the pool"""
        from .module import Module
        if not isinstance(new_module, Module):
            raise RuntimeError("Expecting a Module instance")
        if self.__contains(new_module):
            return False
        if new_module.isfetched:
            for mod in new_module.submodules():
                self._add(mod)
        self.append(new_module)
        return True


    def fetch_all(self):
        """Fetch all the modules declared in the design"""

        def fetch_module(module):
            """Fetch the given module from the remote origin"""
            new_modules = []
            logging.debug("Fetching module: %s", str(module))
            backend = fetch.fetch_type_lookup.get_backend(module)
            fetcher = backend()
            result = fetcher.fetch(module)
            if result is False:
                logging.error("Unable to fetch module %s", str(module.url))
                sys.exit("Exiting")
            module.parse_manifest()
            new_modules.extend(module.local)
            new_modules.extend(module.svn)
            new_modules.extend(module.git)
            return new_modules

        fetch_queue = [m for m in self]

        while len(fetch_queue) > 0:
            cur_mod = fetch_queue.pop()
            new_modules = []
            if cur_mod.isfetched:
                new_modules = cur_mod.submodules()
            else:
                new_modules = fetch_module(cur_mod)
            for mod in new_modules:
                if not mod.isfetched:
                    logging.debug("Appended to fetch queue: "
                        + str(mod.url))
                    self._add(mod)
                    fetch_queue.append(mod)
                else:
                    logging.debug("NOT appended to fetch queue: "
                        + str(mod.url))

