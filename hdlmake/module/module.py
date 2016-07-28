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
import logging

from hdlmake.manifest_parser import ManifestParser
from hdlmake.module import (ModuleSynthesis,
    ModuleSimulation, ModuleContent, ModuleAltera)


class ModuleArgs(object):
    """This class is just a container for the main Module args"""
    def __init__(self):
        self.parent = None
        self.url = None
        self.source = None
        self.fetchto = None

    def set_args(self, parent, url, source, fetchto):
        """Set the module arguments"""
        self.parent = parent
        self.url = url
        self.source = source
        self.fetchto = fetchto

    def get_args(self):
        """Get the module arguments"""
        return self.parent, self.url, self.source, self.fetchto


class Module(ModuleSynthesis,
    ModuleSimulation, ModuleContent, ModuleAltera):
    """
    This is the class providing the HDLMake module, the basic element
    providing the modular behavior allowing for structured designs.
    """

    def __init__(self, module_args, pool):
        """Calculate and initialize the origin attributes: path, source..."""
        assert module_args.url is not None
        assert module_args.source is not None
        super(Module, self).__init__()
        self.init_config(module_args)
        self.set_pool(pool)
        self.module_args = ModuleArgs()
        self.module_args = module_args


    def __str__(self):
        return self.url


    @property
    def is_fetched_to(self):
        """Get the path where the module instance resides"""
        return os.path.dirname(self.path)


    def submodules(self):
        """Get a list with all the submodules this module instance requires"""
        def __nonull(submodule_list):
            """Returns a list with the submodules, being empty if null"""
            if not submodule_list:
                return []
            else:
                return submodule_list
        return __nonull(self.local) + __nonull(self.git) \
            + __nonull(self.svn)


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
        self._set_simulation_options()


    def _set_simulation_options(self):
        """This set the simulation option for all the files in the Module"""
        from hdlmake.srcfile import VerilogFile, VHDLFile
        for file_aux in self.files:
            if isinstance(file_aux, VerilogFile):
                file_aux.vsim_opt = self.sim_opt.vsim_opt
                file_aux.include_dirs = self.include_dirs
            elif isinstance(file_aux, VHDLFile):
                file_aux.vcom_opt = self.sim_opt.vcom_opt
                file_aux.include_dirs = self.include_dirs


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

        logging.debug("""
***********************************************************
PARSE START: %s
***********************************************************""", self.path)

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

        logging.debug("""
***********************************************************
PARSE END: %s
***********************************************************

                      """, self.path)

