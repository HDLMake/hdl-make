#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013, 2014 CERN
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
import logging
import sys
import os
import importlib

from hdlmake.srcfile import SourceFileFactory
from hdlmake.util import path

from .action import Action

class GenerateSynthesisProject(Action):

    def _check_manifest(self):
        if not self.modules_pool.get_top_module().syn_tool:
            logging.error("syn_tool variable must be set in the top manifest.")
            sys.exit("Exiting")
        if not self.modules_pool.get_top_module().manifest_dict["syn_device"]:
            logging.error("syn_device variable must be set in the top manifest.")
            sys.exit("Exiting")
        if not self.modules_pool.get_top_module().manifest_dict["syn_grade"]:
            logging.error("syn_grade variable must be set in the top manifest.")
            sys.exit("Exiting")
        if not self.modules_pool.get_top_module().manifest_dict["syn_package"]:
            logging.error("syn_package variable must be set in the top manifest.")
            sys.exit("Exiting")
        if not self.modules_pool.get_top_module().syn_top:
            logging.error("syn_top variable must be set in the top manifest.")
            sys.exit("Exiting")


    def run(self):
        self._check_all_fetched_or_quit()
        self._check_manifest()
        tool_name = self.modules_pool.get_top_module().syn_tool
        try:
            tool_module = importlib.import_module("hdlmake.tools.%s.%s" % (tool_name, tool_name))
        except Exception as e:
            logging.error(e)
            quit()
        tool_object = tool_module.ToolControls()
        self._generate_synthesis_project(tool_object)


    def _write_project_vhd(self, tool, version):
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
    syn_tool_version => "$syn_tool_version", -- $syn_tool_version_str
    -- Synthesis date (bcd encoded, 32-bit)
    syn_date         => "$syn_date", -- $syn_date_str
    -- Synthesised by (string, 15 char)
    syn_username     => "$syn_username");

end sdb_meta_pkg;

package body sdb_meta_pkg is
end sdb_meta_pkg;""")

        project_vhd = open("project.vhd", 'w')
        date_std_logic_vector = []
        import re 
        for digit in date_string:
            date_std_logic_vector.append("{0:04b}".format(int(digit)))

        syn_tool_version = version
        syn_tool_version = re.sub("\D", "", syn_tool_version)
	syn_tool_std_logic_vector = []
	for digit in syn_tool_version:
	    syn_tool_std_logic_vector.append("{0:04b}".format(int(digit)))

        filled_template = template.substitute(repo_url=self.top_module.url,
                                              syn_module_name=self.top_module.syn_top,
                                              syn_commit_id=self.top_module.revision,
                                              syn_tool_name=tool.upper(),
                                              syn_tool_version="0000"*(8-len(syn_tool_std_logic_vector))+''.join(syn_tool_std_logic_vector),
					      syn_tool_version_str=syn_tool_version,
                                              syn_date=''.join(date_std_logic_vector),
					      syn_date_str=date_string,
                                              syn_username=getpass.getuser())
        project_vhd.write(filled_template)
        project_vhd.close()



    def _generate_synthesis_project(self, tool_object):

        tool_info = tool_object.get_keys()
        if sys.platform == 'cygwin':
            bin_name = tool_info['windows_bin']
        else:
            bin_name = tool_info['linux_bin']
        path_key = tool_info['id'] + '_path'
        version_key = tool_info['id'] + '_version'
        name = tool_info['name']
        id_value = tool_info['id']
        ext_value = tool_info['project_ext']

        env = self.env
        env.check_general()
        env.check_tool(tool_object)

        if not self.options.force:
            if self.env[path_key] is None:
                logging.error("Can't generate the " + name + " project. " + name + " not found.")
                quit()
        if version_key not in env or not env[version_key]:
            logging.error(name + " version cannot be deduced. Cannot generate " + name + " "
                          "project file properly. Please use syn_" + id_value + "_version in the manifest "
                          "or set")
            sys.exit("Exiting")
        logging.info("Generating project for " + name + " v. %s" % env[version_key])
        
        if os.path.exists(self.top_module.syn_project) or os.path.exists(self.top_module.syn_project + "." + ext_value):
            logging.info("Existing project detected: updating...")
            update=True
        else:
            logging.info("No previous project: creating a new one...")
            update=False

        top_mod = self.modules_pool.get_top_module()
        fileset = self.modules_pool.build_file_set()
        privative_files = tool_object.supported_files(self.modules_pool.build_complete_file_set())

        if privative_files:
            logging.info("Privative / non-parseable files detected: %s" % len(privative_files))
            fileset.add(privative_files)

        sff = SourceFileFactory()
        if self.options.generate_project_vhd:
          self._write_project_vhd(id_value, env[version_key])
          fileset.add([sff.new(path=path.rel2abs("project.vhd"),
                                 module=self.modules_pool.get_module_by_path("."))])\


        tool_object.generate_synthesis_project(update=update,
                         tool_version=self.env[version_key],
                         top_mod=self.modules_pool.get_top_module(),
                         fileset = fileset)

        logging.info(name + " project file generated.")



