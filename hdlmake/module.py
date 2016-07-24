#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013-2016 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Multi-tool support by Javier D. Garcia-Lasheras (javier@garcialasheras.com)
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

from __future__ import print_function
import os
import sys
import logging

from .manifest_parser import Manifest, ManifestParser
from .util import path as path_mod
from . import fetch
from .mod import ModuleCore, ModuleSynthesis, ModuleSimulation, ModuleContent, ModuleAltera


class Module(ModuleCore, ModuleSynthesis, ModuleSimulation, ModuleContent, ModuleAltera):
    @property
    def source(self):
        return self._source

    @source.setter
    def source(self, value):
        if value not in [fetch.GIT, fetch.SVN, fetch.LOCAL, fetch.GITSUBMODULE]:
            raise ValueError("Improper source: " + value)
        self._source = value

    @source.deleter
    def source(self):
        del self._source

    @property
    def basename(self):
        from .util import path
        if self.source == fetch.SVN:
            return path.svn_basename(self.url)
        else:
            return path.url_basename(self.url)

    #PLEASE don't use this constructor. Create all modules with ModulePool.new_module()
    def __init__(self, parent, url, source, fetchto, pool):
        assert url is not None
        assert source is not None

        super(Module, self).__init__()

        self.manifest = None
        self.manifest_dict = None
        self.pool = pool
        self.top_module = pool.get_top_module()
        self.source = source
        self.parent = parent
        self.isparsed = False
        self.top_entity = None
        self.fetchto = fetchto

        self.raw_url = url
        if source != fetch.LOCAL:
            self.url, self.branch, self.revision = path_mod.url_parse(url)
            if os.path.exists(os.path.abspath(os.path.join(fetchto, self.basename))) and os.listdir(os.path.abspath(os.path.join(fetchto, self.basename))):
                self.path = os.path.abspath(os.path.join(fetchto, self.basename))
                self.isfetched = True
                logging.debug("Module %s (parent: %s) is fetched." % (url, parent.path))
            else:
                self.path = None
                self.isfetched = False
                logging.debug("Module %s (parent: %s) is NOT fetched." % (url, parent.path))
        else:
            self.url, self.branch, self.revision = url, None, None

            if not os.path.exists(url):
                logging.error("Path to the local module doesn't exist:\n" + url
                              + "\nThis module was instantiated in: " + str(parent))
                quit()
            self.path = url
            self.isfetched = True


    def __str__(self):
        return self.raw_url

    @property
    def is_fetched_to(self):
        return os.path.dirname(self.path)

    def submodules(self):
        def __nonull(x):
            if not x:
                return []
            else:
                return x

        return __nonull(self.local) + __nonull(self.git) + __nonull(self.svn) + __nonull(self.git_submodules)

    def _search_for_manifest(self):
        """
        Look for manifest in the given folder
        """
        logging.debug("Looking for manifest in " + self.path)
        dir_files = os.listdir(self.path)
        if "manifest.py" in dir_files and "Manifest.py" in dir_files:
            logging.error("Both manifest.py and Manifest.py found in the module directory: %s" % self.path)
            sys.exit("\nExiting")
        for filename in dir_files:
            if filename == "manifest.py" or filename == "Manifest.py":
                if not os.path.isdir(filename):
                    logging.debug("Found manifest for module %s: %s" % (self.path, filename))
                    manifest = Manifest(path=os.path.abspath(os.path.join(self.path, filename)))
                    return manifest
        return None

    def _flatten_list(self, sth):
        if sth is not None:
            if not isinstance(sth, (list, tuple)):
                sth = [sth]
        else:
            sth = []
        return sth

    def remove_dir_from_disk(self):
        if not self.isfetched:
            return

        import shutil

        logging.debug("Removing " + self.path)
        shutil.rmtree(self.path)

        while True:
            try:
                logging.debug("Trying to remove " + os.path.dirname(self.path))
                os.rmdir(os.path.dirname(self.path))
            except OSError:  # a catologue is not empty - we are done
                break

    def process_manifest(self):
        logging.debug("Process manifest at: " + os.path.dirname(self.path))
        super(Module, self).process_manifest()


    def parse_manifest(self):
        """
        Create a dictionary from the module Manifest.py and assign it to the manifest_dict property.
        In order to do this, it creates a ManifestParser object and feed it with:
        - the arbitrary code from pool's top_module options (it assumes a top_module exists before any parsing!)
        - the Manifest.py (if exists)
        - the extra_context:
          - If this is the root module (has not parent), use an empty extra_context in the parser
          - If this is a submodule (has a parent), inherit the extra_context as:
            - the full manifest_dict from the top_module...
            - ...but deleting some key fields that needs to be respected (files, modules...).
        """

        if self.manifest_dict:
            return
        if self.isparsed is True or self.isfetched is False:
            return
        if self.manifest is None:
            self.manifest = self._search_for_manifest()
        if self.path is None:
            raise RuntimeError()

        if self.source == fetch.SVN:
            self.revision = fetch.Svn.check_revision_number(self.path)
        elif self.source == fetch.GIT:
            self.revision = fetch.Git.check_commit_id(self.path)

        manifest_parser = ManifestParser()

        #manifest_parser.add_arbitrary_code(self.pool.top_module.options.arbitrary_code)

        if self.manifest is None:
            logging.debug("No manifest found in module "+str(self))
        else:
            logging.debug("Parse manifest in: %s" % self.path)
            manifest_parser.add_manifest(self.manifest)

        if self.parent is None:
            extra_context = {}
        else:
            extra_context = dict(self.top_module.manifest_dict)  # copy the dictionary
            del extra_context["modules"]
            del extra_context["files"]
            del extra_context["include_dirs"]
            del extra_context["sim_only_files"]
            del extra_context["incl_makefiles"]
            del extra_context["library"]
        extra_context["__manifest"] = self.path

        # In the ManifestParser.parse method is where the most of the parser action takes place!
        opt_map = None
        try:
            opt_map = manifest_parser.parse(extra_context=extra_context)
        except NameError as ne:
            logging.error("Error while parsing {0}:\n{1}: {2}.".format(self.manifest, type(ne), ne))
            quit()
        self.manifest_dict = opt_map

        # Process the parsed manifest_dict to assign the module properties
        self.process_manifest()

        # Tag the module as parsed
        self.isparsed = True

        # Parse every detected submodule
        for m in self.submodules():
            m.parse_manifest()


    def _make_list_of_paths(self, list_of_paths):
        paths = []
        for filepath in list_of_paths:
            if self._check_filepath(filepath):
                paths.append(path_mod.rel2abs(filepath, self.path))
        return paths

    def _check_filepath(self, filepath):
        if filepath:
            if path_mod.is_abs_path(filepath):
                logging.warning("Specified path seems to be an absolute path: %s\nOmitting." % filepath)
                return False
            filepath = os.path.join(self.path, filepath)
            if not os.path.exists(filepath):
                logging.error("Path specified in manifest in %s doesn't exist: %s" % (self.path, filepath))
                sys.exit("Exiting")

            filepath = path_mod.rel2abs(filepath, self.path)

            if os.path.isdir(filepath):
                logging.warning("Path specified in manifest %s is a directory: %s" % (self.path, filepath))
        return True


    def _create_file_list_from_paths(self, paths):
        from .srcfile import SourceFileFactory, SourceFileSet
        sff = SourceFileFactory()
        srcs = SourceFileSet()
        for p in paths:
            if os.path.isdir(p):
                dir_ = os.listdir(p)
                for f_dir in dir_:
                    f_dir = os.path.join(self.path, p, f_dir)
                    if not os.path.isdir(f_dir):
                        srcs.add(sff.new(path=f_dir,
                                         module=self,
                                         library=self.library,
                                         vcom_opt=self.vcom_opt,
                                         vlog_opt=self.vlog_opt,
                                         include_dirs=self.include_dirs))
            else:
                srcs.add(sff.new(path=p,
                                 module=self,
                                 library=self.library,
                                 vcom_opt=self.vcom_opt,
                                 vlog_opt=self.vlog_opt,
                                 include_dirs=self.include_dirs))
        return srcs
