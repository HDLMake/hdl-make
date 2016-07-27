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

"""
This python module is the one in charge to support the HDLMake modules
It includes the base Module class, that inherits several action
specific parent modules providing specific methods and attributes.

"""

from __future__ import print_function
import os
import sys
import logging

from hdlmake.manifest_parser import ManifestParser
from hdlmake.util import path as path_mod
from hdlmake import fetch
from hdlmake.module import (ModuleSynthesis, ModuleOrigin,
    ModuleSimulation, ModuleContent, ModuleAltera)


class Module(ModuleSynthesis, ModuleOrigin,
    ModuleSimulation, ModuleContent, ModuleAltera):
    """
    This is the class providing the HDLMake module, the basic element
    providing the modular behavior allowing for structured designs.
    """

    def __init__(self, parent, url, source, fetchto):
        """Calculate and initialize the origin attributes: path, source..."""
        assert url is not None
        assert source is not None
        self.top_entity = None
        self.source = source
        self.parent = parent
        self.set_origin(parent, url, source, fetchto)
        super(Module, self).__init__()



    def __str__(self):
        return self.raw_url


    @property
    def is_fetched_to(self):
        """Get the path where the module instance resides"""
        return os.path.dirname(self.path)


    @property
    def basename(self):
        """Get the basename for a module instance"""
        if self.source == fetch.SVN:
            return path_mod.svn_basename(self.url)
        else:
            return path_mod.url_basename(self.url)


    def submodules(self):
        """Get a list with all the submodules this module instance requires"""
        def __nonull(submodule_list):
            """Returns a list with the submodules, being empty if null"""
            if not submodule_list:
                return []
            else:
                return submodule_list
        return __nonull(self.local) + __nonull(self.git) \
            + __nonull(self.svn) + __nonull(self.git_submodules)


    def remove_dir_from_disk(self):
        """Delete the module dir if it is already fetched and available"""
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
        """
        This method processes the different manifest dictionary sections
        contained in the action specific inherited Python modules.
        """
        logging.debug("Process manifest at: " + os.path.dirname(self.path))
        super(Module, self).process_manifest()
        #module_list = [ModuleSynthesis, ModuleSimulation,
        #    ModuleContent, ModuleAltera]
        #for module_plugin in module_list:
        #    module_plugin.process_manifest(self)


    def parse_manifest(self):
        """
        Create a dictionary from the module Manifest.py and assign it
        to the manifest_dict property.
        In order to do this, it creates a ManifestParser object and
        feeds it with:
        - the arbitrary code from pool's top_module options
            (it assumes a top_module exists before any parsing!)
        - the Manifest.py (if exists)
        - the extra_context:
          - If this is the root module (has not parent),
              use an empty extra_context in the parser
          - If this is a submodule (has a parent),
              inherit the extra_context as:
            - the full manifest_dict from the top_module...
            - ...but deleting some key fields that needs to be respected.
        """

        if self.manifest_dict or self.isfetched is False:
            return
        if self.path is None:
            raise RuntimeError()


        manifest_parser = ManifestParser()

        #manifest_parser.add_arbitrary_code(
        #    self.pool.top_module.options.arbitrary_code)

        manifest_parser.add_manifest(self.path)

        if self.parent is None:
            extra_context = {}
        else:
            extra_context = dict(self.top_module.manifest_dict)
        extra_context["__manifest"] = self.path

        # The parse method is where the most of the parser action takes place!
        opt_map = None
        try:
            opt_map = manifest_parser.parse(extra_context=extra_context)
        except NameError as name_error:
            logging.error(
                "Error while parsing {0}:\n{1}: {2}.".format(
                    self.path, type(name_error), name_error))
            quit()
        self.manifest_dict = opt_map

        # Process the parsed manifest_dict to assign the module properties
        self.process_manifest()

        # Parse every detected submodule
        for module_aux in self.submodules():
            module_aux.parse_manifest()


    def _make_list_of_paths(self, list_of_paths):
        """Get a list with only the valid absolute paths from the provided"""
        paths = []
        for filepath in list_of_paths:
            if self._check_filepath(filepath):
                paths.append(path_mod.rel2abs(filepath, self.path))
        return paths


    def _check_filepath(self, filepath):
        """Check the provided filepath against several conditions"""
        if filepath:
            if path_mod.is_abs_path(filepath):
                logging.warning(
                    "Specified path seems to be an absolute path: " +
                    filepath + "\nOmitting.")
                return False
            filepath = os.path.join(self.path, filepath)
            if not os.path.exists(filepath):
                logging.error(
                    "Path specified in manifest in %s doesn't exist: %s",
                    self.path, filepath)
                sys.exit("Exiting")

            filepath = path_mod.rel2abs(filepath, self.path)
            if os.path.isdir(filepath):
                logging.warning(
                    "Path specified in manifest %s is a directory: %s",
                    self.path, filepath)
        return True


    def _create_file_list_from_paths(self, paths):
        """
        Build a Source File Set containing the files indicated by the
        provided list of paths
        """
        from hdlmake.srcfile import SourceFileFactory, SourceFileSet
        sff = SourceFileFactory()
        srcs = SourceFileSet()
        for path_aux in paths:
            if os.path.isdir(path_aux):
                dir_ = os.listdir(path_aux)
                for f_dir in dir_:
                    f_dir = os.path.join(self.path, path_aux, f_dir)
                    if not os.path.isdir(f_dir):
                        srcs.add(sff.new(path=f_dir,
                                         module=self,
                                         library=self.library,
                                         vcom_opt=self.vcom_opt,
                                         vlog_opt=self.vlog_opt,
                                         include_dirs=self.include_dirs))
            else:
                srcs.add(sff.new(path=path_aux,
                                 module=self,
                                 library=self.library,
                                 vcom_opt=self.vcom_opt,
                                 vlog_opt=self.vlog_opt,
                                 include_dirs=self.include_dirs))
        return srcs



