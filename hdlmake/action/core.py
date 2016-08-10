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

"""This module provides the core actions to the pool"""

import logging
import os
import os.path
import time

import hdlmake.fetch as fetch
import hdlmake.new_dep_solver as dep_solver
from hdlmake.util import path as path_mod
from hdlmake.srcfile import VerilogFile, VHDLFile, NGCFile
from hdlmake.vlog_parser import VerilogPreprocessor
from .action import Action


class ActionCore(Action):

    """Class that contains the methods for core actions"""

    def __init__(self, *args):
        super(ActionCore, self).__init__(*args)

    def fetch(self):
        """Fetch the missing required modules from their remote origin"""
        top_module = self.get_top_module()
        logging.info("Fetching needed modules.")
        os.system(top_module.manifest_dict["fetch_pre_cmd"])
        self.fetch_all()
        os.system(top_module.manifest_dict["fetch_post_cmd"])
        logging.info("All modules fetched.")

    def clean(self):
        """Delete the local copy of the fetched modules"""
        logging.info("Removing fetched modules..")
        remove_list = [mod_aux for mod_aux in self
                       if mod_aux.source in [fetch.GIT, fetch.SVN]
                       and mod_aux.isfetched]
        remove_list.reverse()  # we will remove modules in backward order
        if len(remove_list):
            for mod_aux in remove_list:
                logging.info("... clean: " + mod_aux.url +
                             " [from: " + mod_aux.path + "]")
                mod_aux.remove_dir_from_disk()
        else:
            logging.info("There are no modules to be removed")
        logging.info("Modules cleaned.")

    def list_files(self):
        """List the files added to the design across the pool hierarchy"""
        unfetched_modules = [mod_aux for mod_aux in self
                             if not mod_aux.isfetched]
        for mod_aux in unfetched_modules:
            logging.warning(
                "List incomplete, module %s has not been fetched!", mod_aux)
        file_set = self.build_file_set()
        file_list = dep_solver.make_dependency_sorted_list(file_set)
        files_str = [file_aux.path for file_aux in file_list]
        if self.env.options.delimiter is None:
            delimiter = "\n"
        else:
            delimiter = self.env.options.delimiter
        print delimiter.join(files_str)

    def _print_comment(self, message):
        """Private method that prints a message to stdout if not terse"""
        if not self.env.options.terse:
            print message

    def _print_file_list(self, file_list):
        """Print file list to standard out"""
        if not len(file_list):
            self._print_comment("# * This module has no files")
        else:
            for file_aux in file_list:
                print "%s\t%s" % (
                    path_mod.relpath(file_aux.path), "file")

    def list_modules(self):
        """List the modules that are contained by the pool"""

        def _convert_to_source_name(source_code):
            """Private function that returns a string with the source type"""
            if source_code == fetch.GIT:
                return "git"
            elif source_code == fetch.SVN:
                return "svn"
            elif source_code == fetch.LOCAL:
                return "local"

        for mod_aux in self:
            if not mod_aux.isfetched:
                logging.warning("Module not fetched: %s", mod_aux.url)
                self._print_comment("# MODULE UNFETCHED! -> %s" % mod_aux.url)
            else:
                self._print_comment("# MODULE START -> %s" % mod_aux.url)
                if mod_aux.source in [fetch.SVN, fetch.GIT]:
                    self._print_comment("# * URL: " + mod_aux.url)
                if (mod_aux.source in [fetch.SVN, fetch.GIT, fetch.LOCAL] and
                        mod_aux.parent):
                    self._print_comment("# * The parent for this module is: %s"
                                        % mod_aux.parent.url)
                else:
                    self._print_comment("# * This is the root module")
                print "%s\t%s" % (path_mod.relpath(mod_aux.path),
                                  _convert_to_source_name(mod_aux.source))
                if self.env.options.withfiles:
                    self._print_file_list(mod_aux.files)
                self._print_comment("# MODULE END -> %s" % mod_aux.url)
            self._print_comment("")

    def merge_cores(self):
        """Merge the design into a single VHDL and a single Verilog file"""
        self.check_all_fetched_or_quit()
        logging.info("Merging all cores into one source file per language.")
        flist = self.build_file_set()
        base = self.env.options.dest

        file_header = (
            "\n\n\n\n"
            "------------------------ WARNING --------------------------\n"
            "-- This code has been generated by hdlmake merge-cores   --\n"
            "-- Please DO NOT MODIFY this file. If you need to change --\n"
            "-- something inside, edit the original source file and   --\n"
            "-- re-generate the merged version!                       --\n"
            "-----------------------------------------------------------\n"
            "\n\n\n\n"
        )

        # Generate a VHDL file containing all the required VHDL files
        f_out = open(base + ".vhd", "w")
        f_out.write(file_header)
        for vhdl in flist.filter(VHDLFile):
            f_out.write("\n\n---  File: %s ----\n" % vhdl.rel_path())
            f_out.write("---  Source: %s\n" % vhdl.module.url)
            if vhdl.module.revision:
                f_out.write("---  Revision: %s\n" % vhdl.module.revision)
            f_out.write("---  Last modified: %s\n" %
                        time.ctime(os.path.getmtime(vhdl.path)))
            f_out.write(open(vhdl.rel_path(), "r").read() + "\n\n")
                # print("VHDL: %s" % vhdl.rel_path())
        f_out.close()

        # Generate a VHDL file containing all the required VHDL files
        f_out = open(base + ".v", "w")
        f_out.write(file_header)
        for vlog in flist.filter(VerilogFile):
            f_out.write("\n\n//  File: %s\n" % vlog.rel_path())
            f_out.write("//  Source: %s\n" % vlog.module.url)
            if vlog.module.revision:
                f_out.write("//  Revision: %s\n" % vlog.module.revision)
            f_out.write("//  Last modified: %s\n" %
                        time.ctime(os.path.getmtime(vlog.path)))
            vpp = VerilogPreprocessor()
            for include_path in vlog.include_dirs:
                vpp.add_path(include_path)
            vpp.add_path(vlog.dirname)
            f_out.write(vpp.preprocess(vlog.rel_path()))
        f_out.close()

        # Handling NGC files
        current_path = os.getcwd()
        for ngc in flist.filter(NGCFile):
            import shutil
            logging.info("copying NGC file: %s", ngc.rel_path())
            shutil.copy(ngc.rel_path(), current_path)

        logging.info("Cores merged.")
