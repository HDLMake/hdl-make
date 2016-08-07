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
#

"""Module providing the HDLMake Manifest and its associated parser"""

import os
import logging

from .util import path as path_mod
from .util.configparser import ConfigParser


class ManifestParser(ConfigParser):

    """This is the class providing HDLMake Manifest parser capabilities"""

    def __init__(self):
        ConfigParser.__init__(
            self,
            description="Configuration options description")
        self.add_option(
            'fetchto',
            default=None,
            help="Destination for fetched modules",
            type='')
        self.add_option(
            'fetch_pre_cmd',
            default='',
            help="Command to be executed before fetch",
            type='')
        self.add_option(
            'fetch_post_cmd',
            default='',
            help="Command to be executed after fetch",
            type='')
        self.add_delimiter()
        self.add_option(
            'syn_tool',
            default=None,
            help="Tool to be used in the synthesis",
            type='')
        self.add_option(
            'syn_device',
            default=None,
            help="Target FPGA device",
            type='')
        self.add_option(
            'syn_family',
            default=None,
            help="Target FPGA family",
            type='')
        self.add_option(
            'syn_grade',
            default=None,
            help="Speed grade of target FPGA",
            type='')
        self.add_option(
            'syn_package',
            default=None,
            help="Package variant of target FPGA",
            type='')
        self.add_option(
            'syn_top',
            default=None,
            help="Top level module for synthesis",
            type='')
        self.add_option(
            'syn_project',
            default=None,
            help="Project file (.xise, .ise, .qpf)",
            type='')
        self.add_option(
            'syn_pre_cmd',
            default='',
            help="Command to be executed before synthesis: local",
            type='')
        self.add_option(
            'syn_pre_synthesize_cmd',
            default='',
            help="Command to be executed before synthesis: synthesize",
            type='')
        self.add_option(
            'syn_post_synthesize_cmd',
            default='',
            help="Command to be executed after synthesis: synthesize",
            type='')
        self.add_option(
            'syn_pre_translate_cmd',
            default='',
            help="Command to be executed before synthesis: translate",
            type='')
        self.add_option(
            'syn_post_translate_cmd',
            default='',
            help="Command to be executed after synthesis: translate",
            type='')
        self.add_option(
            'syn_pre_map_cmd',
            default='',
            help="Command to be executed before synthesis: map",
            type='')
        self.add_option(
            'syn_post_map_cmd',
            default='',
            help="Command to be executed after synthesis: map",
            type='')
        self.add_option(
            'syn_pre_par_cmd',
            default='',
            help="Command to be executed before synthesis: par",
            type='')
        self.add_option(
            'syn_post_par_cmd',
            default='',
            help="Command to be executed after synthesis: par",
            type='')
        self.add_option(
            'syn_pre_bitstream_cmd',
            default='',
            help="Command to be executed before synthesis: bitstream",
            type='')
        self.add_option(
            'syn_post_bitstream_cmd',
            default='',
            help="Command to be executed after synthesis: bitstream",
            type='')
        self.add_option(
            'syn_post_cmd',
            default='',
            help="Command to be executed after synthesis: local",
            type='')
        self.add_delimiter()
        self.add_option(
            'top_module',
            default=None,
            help="Top level entity for synthesis and simulation",
            type='')
        self.add_delimiter()
        self.add_option(
            'quartus_preflow',
            default=None,
            help="Quartus pre-flow script file",
            type='')
        self.add_option(
            'quartus_postmodule',
            default=None,
            help="Quartus post-module script file",
            type='')
        self.add_option(
            'quartus_postflow',
            default=None,
            help="Quartus post-flow script file",
            type='')
        self.add_delimiter()
        self.add_option(
            'include_dirs',
            default=None,
            help="Include dirs for Verilog sources",
            type=[])
        self.add_type('include_dirs', type="")
        self.add_delimiter()
        self.add_option(
            'sim_top',
            default=None,
            help="Top level module for simulation",
            type='')
        self.add_option(
            'sim_tool',
            default=None,
            help="Simulation tool to be used (e.g. isim, vsim, iverilog)",
            type='')
        self.add_option(
            'sim_pre_cmd',
            default=None,
            help="Command to be executed before simulation",
            type='')
        self.add_option(
            'sim_post_cmd',
            default=None,
            help="Command to be executed after simulation",
            type='')
        self.add_option(
            'vsim_opt',
            default="",
            help="Additional options for vsim",
            type='')
        self.add_option(
            'vcom_opt',
            default="",
            help="Additional options for vcom",
            type='')
        self.add_option(
            'vlog_opt',
            default="",
            help="Additional options for vlog",
            type='')
        self.add_option(
            'vmap_opt',
            default="",
            help="Additional options for vmap",
            type='')
        self.add_delimiter()
        self.add_option(
            'iverilog_opt',
            default="",
            help="Additional options for IVerilog",
            type='')
        self.add_option(
            'ghdl_opt',
            default="",
            help="Additional options for GHDL",
            type='')
        self.add_delimiter()
        self.add_option(
            'modules',
            default={},
            help="List of local modules",
            type={})
        self.add_allowed_key('modules', key="svn")
        self.add_allowed_key('modules', key="git")
        self.add_allowed_key('modules', key="local")
        self.add_option(
            'action',
            default='',
            help="What is the action that should be taken if "
                 "HDLMake is run in auto mode (simulation/synthesis)",
            type='')
        # self.add_delimiter()
        self.add_option('library', default="work",
                        help="Destination library for module's VHDL files",
                        type="")
        self.add_option(
            'files',
            default=[],
            help="List of files from the current module",
            type='')
        self.add_type('files', type=[])
        self.add_option(
            'incl_makefiles',
            default=[],
            help="List of .mk files appended to toplevel makefile",
            type=[])
        self.add_type('incl_makefiles', type='')

    def add_manifest(self, path):
        """Add to configuration the Manifest at directory (path) if exists"""
        def _search_for_manifest(path):
            """
            Look for manifest in the given folder and create a Manifest object
            """
            logging.debug("Looking for manifest in " + path)
            dir_files = os.listdir(path)
            if "manifest.py" in dir_files and "Manifest.py" in dir_files:
                logging.error(
                    "Both manifest.py and Manifest.py" +
                    "found in the module directory: %s",
                    path)
                quit()
            for filename in dir_files:
                if filename == "manifest.py" or filename == "Manifest.py":
                    if not os.path.isdir(filename):
                        logging.debug("Found manifest for module %s: %s",
                                      path, filename)
                        path_aux = os.path.join(path, filename)
                        if not isinstance(path_aux, str):
                            raise ValueError("Path must be an instance of str")
                        if not path_mod.is_abs_path(path_aux):
                            raise ValueError(
                                "Manifest path must be absolute path")
                        return path_aux
            return None
        manifest = _search_for_manifest(path)
        if manifest is None:
            logging.error("No manifest found in path: %s", path)
            quit()
        else:
            logging.debug("Parse manifest in: %s", manifest)
            return self.add_config_file(manifest)

    def print_help(self):
        """Print the help for the Manifest parser object"""
        self.help()

