#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 - 2015 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Modified to allow ISim simulation by Lucas Russo (lucas.russo@lnls.br)
# Modified to allow ISim simulation by Adrian Byszuk (adrian.byszuk@lnls.br)
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

"""Module providing support for Xilinx ISim simulator"""

from __future__ import absolute_import
import os
import os.path
import logging

from .make_sim import ToolSim
from hdlmake.util import shell
from hdlmake.srcfile import VerilogFile, VHDLFile


class ToolISim(ToolSim):

    """Class providing the interface for Xilinx ISim simulator"""

    TOOL_INFO = {
        'name': 'ISim',
        'id': 'isim',
        'windows_bin': 'isimgui.exe',
        'linux_bin': 'isimgui'}

    STANDARD_LIBS = ['std', 'ieee', 'ieee_proposed', 'vl', 'synopsys',
                     'simprim', 'unisim', 'unimacro', 'aim', 'cpld',
                     'pls', 'xilinxcorelib', 'aim_ver', 'cpld_ver',
                     'simprims_ver', 'unisims_ver', 'uni9000_ver',
                     'unimacro_ver', 'xilinxcorelib_ver', 'secureip']

    HDL_FILES = {VerilogFile: '', VHDLFile: ''}

    CLEAN_TARGETS = {'clean': ["xilinxsim.ini $(LIBS)", "fuse.xmsgs",
                               "fuse.log", "fuseRelaunch.cmd", "isim",
                               "isim.log", "isim.wdb", "isim_proj",
                               "isim_proj.*"],
                     'mrproper': ["*.vcd"]}

    def __init__(self):
        super(ToolISim, self).__init__()
        self._tool_info.update(ToolISim.TOOL_INFO)
        self._hdl_files.update(ToolISim.HDL_FILES)
        self._standard_libs.extend(ToolISim.STANDARD_LIBS)
        self._clean_targets.update(ToolISim.CLEAN_TARGETS)

    def _makefile_sim_top(self):
        """Print the top section of the Makefile for Xilinx ISim"""

        def __get_xilinxsim_ini_dir():
            """Get Xilinx ISim ini simulation file"""
            if "sim_path" in self.manifest_dict:
                xilinx_dir = str(os.path.join(
                    self.manifest_dict["sim_path"], "..", ".."))
            else:
                logging.error("Cannot calculate xilinx tools base directory")
                quit()
            hdl_language = 'vhdl'  # 'verilog'
            if shell.check_windows():
                os_prefix = 'nt'
            else:
                os_prefix = 'lin'
            if shell.architecture() == 32:
                arch_sufix = ''
            else:
                arch_sufix = '64'
            xilinx_ini_path = str(os.path.join(xilinx_dir,
                                  hdl_language,
                                  "hdp",
                                  os_prefix + arch_sufix))
            # Ensure the path is absolute and normalized
            return os.path.abspath(xilinx_ini_path)
        self.writeln("""## variables #############################
PWD := $(shell pwd)
TOP_MODULE := """ + self.manifest_dict.get("sim_top", '') + """
FUSE_OUTPUT ?= isim_proj

XILINX_INI_PATH := """ + __get_xilinxsim_ini_dir() +
                     """
""")

    def _makefile_sim_options(self):
        """Print the Xilinx ISim simulation options in the Makefile"""
        def __get_rid_of_isim_incdirs(vlog_opt):
            """Clean the vlog options from include dirs"""
            if not vlog_opt:
                vlog_opt = ""
            vlogs = vlog_opt.split(' ')
            ret = []
            skip = False
            for vlog_option in vlogs:
                if skip:
                    skip = False
                    continue
                if not vlog_option.startswith("-i"):
                    ret.append(vlog_option)
                else:
                    skip = True
            return ' '.join(ret)
        default_options = ("-intstyle default -incremental " +
                           "-initfile xilinxsim.ini ")
        self.writeln("VHPCOMP_FLAGS := " +
            default_options + self.manifest_dict.get("vcom_opt", ''))
        self.writeln("VLOGCOMP_FLAGS := " +
            default_options + __get_rid_of_isim_incdirs(
            self.manifest_dict.get("vlog_opt", '')))

    def _makefile_sim_compilation(self):
        """Print the compile simulation target for Xilinx ISim"""
        fileset = self.fileset
        libs = set(f.library for f in fileset)
        self.write('LIBS := ')
        self.write(' '.join(libs))
        self.write('\n')
        # tell how to make libraries
        self.write('LIB_IND := ')
        self.write(' '.join([lib + shell.slash_char() +
            "." + lib for lib in libs]))
        self.write('\n')
        self.writeln("""\
simulation: xilinxsim.ini $(LIB_IND) $(VERILOG_OBJ) $(VHDL_OBJ) fuse
$(VERILOG_OBJ): $(LIB_IND) xilinxsim.ini
$(VHDL_OBJ): $(LIB_IND) xilinxsim.ini

""")
        self.writeln("xilinxsim.ini: $(XILINX_INI_PATH)" +
            shell.slash_char() + "xilinxsim.ini")
        self.writeln("\t\t" + shell.copy_command() + " $< .")
        self.writeln("""\
fuse:
\t\tfuse work.$(TOP_MODULE) -intstyle ise -incremental -o $(FUSE_OUTPUT)

""")
        # ISim does not have a vmap command to insert additional libraries in
        #.ini file.
        for lib in libs:
            self.write(lib + shell.slash_char() + "." + lib + ":\n")
            self.write(
                ' '.join(["\t(" + shell.mkdir_command(), lib, "&&",
                          shell.touch_command(),
                          lib + shell.slash_char() + "." + lib + " "]))
            # self.write(' '.join(["&&", "echo", "\""+lib+"="+lib+"/."+lib+"\"
            # ", ">>", "xilinxsim.ini) "]))
            self.write(
                ' '.join(["&&",
                          "echo",
                          lib + "=" + lib,
                          " >>",
                          "xilinxsim.ini) "]))
            self.write(' '.join(["||", shell.del_command(), lib, "\n"]))
            self.write('\n')
            # Modify xilinxsim.ini file by including the extra local libraries
            # self.write(' '.join(["\t(echo """, lib+"="+lib+"/."+lib, ">>",
            # "${XILINX_INI_PATH}/xilinxsim.ini"]))
        # rules for all _primary.dat files for sv
        # incdir = ""
        objs = []
        for vl_file in fileset.filter(VerilogFile):
            comp_obj = os.path.join(vl_file.library, vl_file.purename)
            objs.append(comp_obj)
            # self.write(os.path.join(vl_file.library, vl_file.purename,
            #            '.'+vl_file.purename+"_"+vl_file.extension())+': ')
            # self.writeln(".PHONY: " + os.path.join(comp_obj,
            # '.'+vl_file.purename+"_"+vl_file.extension()))
            self.write(
                os.path.join(
                    comp_obj,
                    '.' +
                    vl_file.purename +
                    "_" +
                    vl_file.extension(
                    )) +
                ': ')
            self.write(vl_file.rel_path() + ' ')
            self.writeln(
                ' '.join([fname.rel_path() for fname in vl_file.depends_on]))
            self.write("\t\tvlogcomp -work " + vl_file.library
                       + "=." + shell.slash_char() + vl_file.library)
            self.write(" $(VLOGCOMP_FLAGS) ")
            # if isinstance(vl_file, SVFile):
            #    self.write(" -sv ")
            # incdir = "-i "
            # incdir += " -i ".join(vl_file.include_dirs)
            # incdir += " "
            if vl_file.include_dirs:
                self.write(' -i ')
                self.write(' '.join(vl_file.include_dirs))
            self.writeln(" $<")
            self.write("\t\t@" + shell.mkdir_command() + " $(dir $@)")
            self.writeln(" && " + shell.touch_command() + " $@ \n\n")
        self.write("\n")
        # list rules for all _primary.dat files for vhdl
        for vhdl_file in fileset.filter(VHDLFile):
            lib = vhdl_file.library
            purename = vhdl_file.purename
            comp_obj = os.path.join(lib, purename)
            objs.append(comp_obj)
            # each .dat depends on corresponding .vhd file and its dependencies
            # self.write(os.path.join(lib, purename, "."+purename+"_"
            #     + vhdl_file.extension()) + ": "+ vhdl_file.rel_path()+" "
            #     + os.path.join(lib, purename, "."+purename) + '\n')
            # self.writeln(".PHONY: " + os.path.join(comp_obj,
            # "."+purename+"_"+ vhdl_file.extension()))
            self.write(
                os.path.join(
                    comp_obj,
                    "." + purename + "_" + vhdl_file.extension(
                    )) + ": " + vhdl_file.rel_path(
                ) + " " + os.path.join(
                    lib,
                    purename,
                    "." + purename) + '\n')
            self.writeln(
                ' '.join(["\t\tvhpcomp $(VHPCOMP_FLAGS)",
                          "-work",
                          lib + "=." + shell.slash_char() + lib,
                          "$< "]))
            self.writeln("\t\t@" + shell.mkdir_command() +
                         " $(dir $@) && " + shell.touch_command() + " $@\n")
            self.writeln()
            # dependency meta-target.
            # This rule just list the dependencies of the above file
            # if len(vhdl_file.depends_on) != 0:
            # self.writeln(".PHONY: " + os.path.join(
            #     lib, purename, "."+purename))
            # Touch the dependency file as well. In this way, "make" will
            # recompile only what is needed (out of date)
            # if len(vhdl_file.depends_on) != 0:
            self.write(os.path.join(lib, purename, "." + purename) + ":")
            for dep_file in vhdl_file.depends_on:
                if dep_file in fileset:
                    name = dep_file.purename
                    self.write(
                        " \\\n" + os.path.join(dep_file.library,
                                               name, "." + name + "_" +
                                               vhdl_file.extension()))
                else:
                    self.write(" \\\n" + os.path.join(dep_file.rel_path()))
            self.write('\n')
            self.writeln("\t\t@" + shell.mkdir_command() +
                         " $(dir $@) && " + shell.touch_command() + " $@\n")
