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

import os
import os.path
from subprocess import Popen, PIPE
import logging
import sys

from hdlmake.util import path as path_mod
from hdlmake.action import ActionMakefile
from hdlmake.srcfile import VerilogFile, VHDLFile


ISIM_STANDARD_LIBS = ['std', 'ieee', 'ieee_proposed', 'vl', 'synopsys',
                      'simprim', 'unisim', 'unimacro', 'aim', 'cpld',
                      'pls', 'xilinxcorelib', 'aim_ver', 'cpld_ver',
                      'simprims_ver', 'unisims_ver', 'uni9000_ver',
                      'unimacro_ver', 'xilinxcorelib_ver', 'secureip']


class ToolISim(ActionMakefile):

    """Class providing the interface for Xilinx ISim simulator"""

    TOOL_INFO = {
        'name': 'ISim',
        'id': 'isim',
        'windows_bin': 'isimgui',
        'linux_bin': 'isimgui'}

    SUPPORTED_FILES = []

    CLEAN_TARGETS = {'clean': ["./xilinxsim.ini $(LIBS)", "fuse.xmsgs",
                               "fuse.log", "fuseRelaunch.cmd", "isim",
                               "isim.log", "isim.wdb", "isim_proj",
                               "isim_proj.*"],
                     'mrproper': ["*.vcd"]}

    def __init__(self):
        super(ToolISim, self).__init__()

    def detect_version(self, path):
        """Get version from Xilinx ISim simulator program"""
        is_windows = path_mod.check_windows()
        isim = Popen(
            "%s --version | awk '{print $2}'" % os.path.join(path, "vlogcomp"),
            shell=True,
            close_fds=not is_windows,
            stdin=PIPE,
            stdout=PIPE)
        print os.path.join(path, "vlogcomp")
        try:
            isim_version = isim.stdout.readlines()[0].strip()
        except:
            return None
        return isim_version

    def makefile_sim_top(self, top_module):
        """Print the top section of the Makefile for Xilinx ISim"""
        self.writeln("""## variables #############################
PWD := $(shell pwd)
TOP_MODULE := """ + top_module.manifest_dict["sim_top"] + """
FUSE_OUTPUT ?= isim_proj

XILINX_INI_PATH := """ + self.__get_xilinxsim_ini_dir(top_module.pool.env) +
                     """
""")

    def makefile_sim_options(self, top_module):
        """Print the Xilinx ISim simulation options in the Makefile"""
        self.writeln("""VHPCOMP_FLAGS := -intstyle default \
-incremental -initfile xilinxsim.ini
ISIM_FLAGS :=
VLOGCOMP_FLAGS := -intstyle default -incremental -initfile xilinxsim.ini """ +
                     self.__get_rid_of_isim_incdirs(
                     top_module.manifest_dict["vlog_opt"]) + """
""")

    def makefile_sim_compilation(self, fileset, top_module):
        """Print the compile simulation target for Xilinx ISim"""
        make_preambule_p2 = """## rules #################################
simulation: xilinxsim.ini $(LIB_IND) $(VERILOG_OBJ) $(VHDL_OBJ) fuse
$(VERILOG_OBJ): $(LIB_IND) xilinxsim.ini
$(VHDL_OBJ): $(LIB_IND) xilinxsim.ini

xilinxsim.ini: $(XILINX_INI_PATH)/xilinxsim.ini
\t\tcp $< .
fuse:
\t\tfuse work.$(TOP_MODULE) -intstyle ise -incremental -o $(FUSE_OUTPUT)

"""

        libs = set(f.library for f in fileset)

        self.write('LIBS := ')
        self.write(' '.join(libs))
        self.write('\n')
        # tell how to make libraries
        self.write('LIB_IND := ')
        self.write(' '.join([lib + "/." + lib for lib in libs]))
        self.write('\n')

        self.writeln(make_preambule_p2)

        # ISim does not have a vmap command to insert additional libraries in
        #.ini file.
        for lib in libs:
            self.write(lib + "/." + lib + ":\n")
            self.write(
                ' '.join(["\t(mkdir", lib, "&&", "touch",
                          lib + "/." + lib + " "]))
            # self.write(' '.join(["&&", "echo", "\""+lib+"="+lib+"/."+lib+"\"
            # ", ">>", "xilinxsim.ini) "]))
            self.write(
                ' '.join(["&&",
                          "echo",
                          "\"" + lib + "=" + lib + "\" ",
                          ">>",
                          "xilinxsim.ini) "]))
            self.write(' '.join(["||", "rm -rf", lib, "\n"]))
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
                       + "=./" + vl_file.library)
            self.write(" $(VLOGCOMP_FLAGS) ")
            # if isinstance(vl_file, SVFile):
            #    self.write(" -sv ")
            # incdir = "-i "
            # incdir += " -i ".join(vl_file.include_dirs)
            # incdir += " "
            if vl_file.include_dirs:
                self.write(' -i ')
                self.write(' '.join(vl_file.include_dirs) + ' ')
            self.writeln(vl_file.vlog_opt + " $<")
            self.write("\t\t@mkdir -p $(dir $@)")
            self.writeln(" && touch $@ \n\n")
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
                          vhdl_file.vcom_opt,
                          "-work",
                          lib + "=./" + lib,
                          "$< "]))
            self.writeln("\t\t@mkdir -p $(dir $@) && touch $@\n")
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
            self.writeln("\t\t@mkdir -p $(dir $@) && touch $@\n")

    def __get_rid_of_isim_incdirs(self, vlog_opt):
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

    def __get_xilinxsim_ini_dir(self, env):
        """Get Xilinx ISim ini simulation file"""
        if env["isim_path"]:
            xilinx_dir = str(os.path.join(env["isim_path"], "..", ".."))
        else:
            logging.error("Cannot calculate xilinx tools base directory")
            quit()
        hdl_language = 'vhdl'  # 'verilog'
        if sys.platform == 'cygwin':
            os_prefix = 'nt'
        else:
            os_prefix = 'lin'
        if env["architecture"] == 32:
            arch_sufix = ''
        else:
            arch_sufix = '64'
        xilinx_ini_path = str(os.path.join(xilinx_dir,
                              hdl_language,
                              "hdp",
                              os_prefix + arch_sufix))
        # Ensure the path is absolute and normalized
        return os.path.abspath(xilinx_ini_path)
