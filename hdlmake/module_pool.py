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
#

from __future__ import print_function
import os
import logging
import global_mod
import sys
import new_dep_solver as dep_solver
from util import path as path_mod
from fetch import BackendFactory
import fetch
from subprocess import PIPE, Popen


class ModulePool(list):
    def __init__(self, *args):
        list.__init__(self, *args)
        self.top_module = None
        self.global_fetch = os.getenv("HDLMAKE_COREDIR")

    def get_module_by_path(self, path):
        path = path_mod.rel2abs(path)
        for module in self:
            if module.path == path:
                return module
        return None

    def get_fetchable_modules(self):
        return [m for m in self if m.source != fetch.LOCAL]

    def __str__(self):
        return str([str(m) for m in self])

    def __contains(self, module):
        for mod in self:
            if mod.url == module.url:
                return True
        return False


    def new_module(self, parent, url, source, fetchto, process_manifest=True):
        from module import Module
        if source != fetch.LOCAL:
            clean_url, branch, revision = path_mod.url_parse(url)
        else:
            clean_url, branch, revision = url, None, None
        if url in [m.raw_url for m in self]:  # check if module is not already in the pool
            # same_url_mod = [m for m in self if m.raw_url == url][0]
            # if branch != same_url_mod.branch:
            #     logging.error("Requested the same module, but different branches."
            #                   "URL: %s\n" % clean_url +
            #                   "branches: %s and %s\n" % (branch, same_url_mod.branch))
            #     sys.exit("\nExiting")
            # if revision != same_url_mod.revision:
            #     logging.error("Requested the same module, but different revisions."
            #                   "URL: %s\n" % clean_url +
            #                   "revisions: %s (from %s)\n and \n%s (from %s)\n" % (revision,
            #                                                                       parent.path,
            #                                                                       same_url_mod.revision,
            #                                                                       same_url_mod.parent.path))
            #     sys.exit("\nExiting")
            return [m for m in self if m.raw_url == url][0]
        else:
            if self.global_fetch:            # if there is global fetch parameter (HDLMAKE_COREDIR env variable)
                fetchto = self.global_fetch  # screw module's particular fetchto

            new_module = Module(parent=parent,
                                url=url, source=source,
                                fetchto=fetchto,
                                pool=self)
            self._add(new_module)
            if not self.top_module:
                global_mod.top_module = new_module
                self.top_module = new_module
                new_module.parse_manifest()
                if process_manifest is True:
                    new_module.process_manifest()
            return new_module

    def process_top_module_manifest(self):
        url = self._guess_origin(global_mod.top_module.path)
        if url:
            global_mod.top_module.url = url
        global_mod.top_module.process_manifest()

    def _guess_origin(self, path):
        cwd = os.getcwd()
        try:
            os.chdir(path)
            git_out = Popen("git config --get remote.origin.url", stdout=PIPE, shell=True, close_fds=True)
            lines = git_out.stdout.readlines()
            if len(lines) == 0:
                return None
            url = lines[0].strip()
            if not url:  # try svn
                svn_out = Popen("svn info | grep 'Repository Root' | awk '{print $NF}'", stdout=PIPE, shell=True, close_fds=True)
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
        from module import Module
        if not isinstance(new_module, Module):
            raise RuntimeError("Expecting a Module instance")
        if self.__contains(new_module):
            return False
        if new_module.isfetched:
            for mod in new_module.submodules():
                self._add(mod)
        self.append(new_module)
        return True

    def _fetch(self, module):
        new_modules = []
        logging.debug("Fetching module: " + str(module))

        bf = BackendFactory()
        fetcher = bf.get_backend(module)
        result = fetcher.fetch(module)
        if result is False:
            logging.error("Unable to fetch module %s" % module.url)
            sys.exit("Exiting")

        module.parse_manifest()
        module.process_manifest()

        new_modules.extend(module.local)
        new_modules.extend(module.svn)
        new_modules.extend(module.git)
        new_modules.extend(module.git_submodules)
        return new_modules

    def fetch_all(self, unfetched_only=False, flatten=False):
        fetch_queue = [m for m in self]

        while len(fetch_queue) > 0:
            cur_mod = fetch_queue.pop()
            if flatten is True:
                cur_mod.fetchto = global_mod.top_module.fetchto
            new_modules = []
            if unfetched_only:
                if cur_mod.isfetched:
                    new_modules = cur_mod.submodules()
                else:
                    new_modules = self._fetch(cur_mod)
            else:
                new_modules = self._fetch(cur_mod)
            for mod in new_modules:
                if not mod.isfetched:
                    logging.debug("Appended to fetch queue: " + str(mod.url))
                    self._add(mod)
                    fetch_queue.append(mod)
                else:
                    logging.debug("NOT appended to fetch queue: " + str(mod.url))

    def build_global_file_list(self):
        from srcfile import SourceFileSet
        ret = SourceFileSet()
        for module in self:
            ret.add(module.files)
        return ret

    def build_very_global_file_list(self):
        from srcfile import SourceFileSet   
        files = self.build_global_file_list()
        assert isinstance(files, SourceFileSet)
        dep_solver.solve(files)
        ret = []
        for file in files:
            try:
                for dep_file in file.dep_depends_on:
                    if dep_file not in ret:
                        ret.add(dep_file)
                ret.add(file)
            except:
                pass
        return files

    def get_top_module(self):
        return self.top_module

    def is_everything_fetched(self):
        if len([m for m in self if not m.isfetched]) == 0:
            return True
        else:
            return False
