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

from __future__ import print_function
import logging
from action import Action
import sys
import os
import new_dep_solver as dep_solver
from tools.ise import ISEProject
from srcfile import SourceFileFactory
import global_mod
from util import path


class GenerateISEProject(Action):
    def _check_manifest(self):
       # self._check_manifest_variable_is_set("top_module")
        self._check_manifest_variable_is_set("syn_device")
        self._check_manifest_variable_is_set("syn_grade")
        self._check_manifest_variable_is_set("syn_package")
        self._check_manifest_variable_is_set("syn_top")

    def _check_env(self):
        env = self.env
        if self.env["ise_path"] is None:
            logging.error("Can't generate an ISE project. ISE not found.")
            quit()
        else:
            if not env["ise_version"]:
                logging.error("Xilinx version cannot be deduced. Cannot generate ISE "
                              "project file properly. Please use syn_ise_version in the manifest "
                              "or set")
                sys.exit("Exiting")
            else:
                logging.info("Generating project for ISE v. %s" % env["ise_version"])

    def _to_bcd(self, integer):
        assert integer >= 0 and integer <= 0


    def run(self):
        self._check_all_fetched_or_quit()
        logging.info("Generating/updating ISE project file.")
        if os.path.exists(self.top_module.syn_project) or os.path.exists(self.top_module.syn_project + ".xise"):
            self._handle_ise_project(update=True)
        else:
            self._handle_ise_project(update=False)
        logging.info("ISE project file generated.")

    def _handle_ise_project(self, update=False):
        top_mod = self.modules_pool.get_top_module()
        fileset = self.modules_pool.build_file_set()
        flist = dep_solver.make_dependency_sorted_list(fileset)
        assert isinstance(flist, list)

        prj = ISEProject(ise=self.env["ise_version"],
                         top_mod=self.modules_pool.get_top_module())
        prj.add_files(flist)
        sff = SourceFileFactory()
        logging.debug(top_mod.vlog_opt)

        if self.options.generate_project_vhd:
          self._write_project_vhd()
          prj.add_files([sff.new(path=path.rel2abs("project.vhd"),
                                 module=self.modules_pool.get_module_by_path("."))])\

        prj.add_libs(fileset.get_libs())
        if update is True:
            try:
                prj.load_xml(top_mod.syn_project)
            except:
                logging.error("Error while reading the project file.\n"
                              "Are you sure that syn_project indicates a correct ISE project file?")
                raise
        else:
            prj.add_initial_properties()
        logging.info("Writing down .xise project file")
        prj.emit_xml(top_mod.syn_project)

    def _write_project_vhd(self):
        from string import Template
        from datetime import date
        import getpass

        today = date.today()
        date_string = today.strftime("%Y%m%d")
        template = Template("""library ieee;
use work.wishbone_pkg.all;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

package sdb_meta_pkg is

  ------------------------------------------------------------------------------
  -- Meta-information sdb records
  ------------------------------------------------------------------------------

  -- Top module repository url
  constant c_SDB_REPO_URL : t_sdb_repo_url := (
    -- url (string, 63 char)
    repo_url => "$repo_url");

  -- Synthesis informations
  constant c_SDB_SYNTHESIS : t_sdb_synthesis := (
    -- Top module name (string, 16 char)
    syn_module_name  => "$syn_module_name",
    -- Commit ID (hex string, 128-bit = 32 char)
    -- git log -1 --format="%H" | cut -c1-32
    syn_commit_id    => "$syn_commit_id",
    -- Synthesis tool name (string, 8 char)
    syn_tool_name    => "$syn_tool_name",
    -- Synthesis tool version (bcd encoded, 32-bit)
    syn_tool_version => "$syn_tool_version",
    -- Synthesis date (bcd encoded, 32-bit)
    syn_date         => "$syn_date",
    -- Synthesised by (string, 15 char)
    syn_username     => "$syn_username");

end sdb_meta_pkg;

package body sdb_meta_pkg is
end sdb_meta_pkg;""")

        project_vhd = open("project.vhd", 'w')
        date_std_logic_vector = []
        import re 
        for digit in date_string:
            date_std_logic_vector.append("{0:b}".format(int(digit)))

        syn_tool_version = global_mod.env["ise_version"]
        syn_tool_version = re.sub("\D", "", syn_tool_version)

        filled_template = template.substitute(repo_url=global_mod.top_module.url,
                                              syn_module_name=global_mod.top_module.top_module,
                                              syn_commit_id=global_mod.top_module.revision,
                                              syn_tool_name="ISE",
                                              syn_tool_version=global_mod.env["ise_version"],
                                              syn_date=''.join(date_std_logic_vector),
                                              syn_username=getpass.getuser())
        project_vhd.write(filled_template)
        project_vhd.close()
