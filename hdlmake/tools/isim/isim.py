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

import os
import os.path
from subprocess import Popen, PIPE
import logging
import sys
import string
import platform

from hdlmake.makefile_writer import MakefileWriter


ISIM_STANDARD_LIBS = ['std', 'ieee', 'ieee_proposed', 'vl', 'synopsys',
                      'simprim', 'unisim', 'unimacro', 'aim', 'cpld',
                      'pls', 'xilinxcorelib', 'aim_ver', 'cpld_ver',
                      'simprims_ver', 'unisims_ver', 'uni9000_ver',
                      'unimacro_ver', 'xilinxcorelib_ver', 'secureip']

class ToolControls(MakefileWriter):

    def get_keys(self):
        tool_info = {
            'name': 'ISim',
            'id': 'isim',
            'windows_bin': 'isimgui',
            'linux_bin': 'isimgui'
        }
        return tool_info

    def get_standard_libraries(self):
        return ISIM_STANDARD_LIBS

    def detect_version(self, path):
        if platform.system() == 'Windows': is_windows = True
        else: is_windows = False
        isim = Popen("%s --version | awk '{print $2}'" % os.path.join(path, "vlogcomp"),
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


    def supported_files(self, fileset):
        from hdlmake.srcfile import SourceFileSet
        sup_files = SourceFileSet()
        return sup_files


    def generate_simulation_makefile(self, fileset, top_module):
        from hdlmake.srcfile import VerilogFile, VHDLFile
        make_preambule_p1 = """## variables #############################
PWD := $(shell pwd)
TOP_MODULE := """ + top_module.top_entity + """
FUSE_OUTPUT ?= isim_proj

XILINX_INI_PATH := """ + self.__get_xilinxsim_ini_dir(top_module.pool.env) + """

VHPCOMP_FLAGS := -intstyle default -incremental -initfile xilinxsim.ini
ISIM_FLAGS :=
VLOGCOMP_FLAGS := -intstyle default -incremental -initfile xilinxsim.ini """ + self.__get_rid_of_isim_incdirs(top_module.manifest_dict["vlog_opt"]) + """
"""
        make_preambule_p2 = string.Template("""## rules #################################
local: sim_pre_cmd simulation sim_post_cmd

simulation: xilinxsim.ini $$(LIB_IND) $$(VERILOG_OBJ) $$(VHDL_OBJ) fuse
$$(VERILOG_OBJ): $$(LIB_IND) xilinxsim.ini
$$(VHDL_OBJ): $$(LIB_IND) xilinxsim.ini

sim_pre_cmd:
\t\t${sim_pre_cmd}

sim_post_cmd:
\t\t${sim_post_cmd}

xilinxsim.ini: $$(XILINX_INI_PATH)/xilinxsim.ini
\t\tcp $$< .
fuse:
\t\tfuse work.$$(TOP_MODULE) -intstyle ise -incremental -o $$(FUSE_OUTPUT)

clean:
\t\trm -rf ./xilinxsim.ini $$(LIBS) fuse.xmsgs fuse.log fuseRelaunch.cmd isim isim.log \
isim.wdb isim_proj isim_proj.*
.PHONY: clean sim_pre_cmd sim_post_cmd simulation

""")
        #open the file and write the above preambule (part 1)
        self.write(make_preambule_p1)

        self.write("VERILOG_SRC := ")
        for vl in fileset.filter(VerilogFile):
            self.write(vl.rel_path() + " \\\n")
        self.write("\n")

        self.write("VERILOG_OBJ := ")
        for vl in fileset.filter(VerilogFile):
            #make a file compilation indicator (these .dat files are made even if
            #the compilation process fails) and add an ending according to file's
            #extension (.sv and .vhd files may have the same corename and this
            #causes a mess
            self.write(os.path.join(vl.library, vl.purename, "."+vl.purename+"_"+vl.extension()) + " \\\n")
        self.write('\n')

        libs = set(f.library for f in fileset)

        self.write("VHDL_SRC := ")
        for vhdl in fileset.filter(VHDLFile):
            self.write(vhdl.rel_path() + " \\\n")
        self.writeln()

        #list vhdl objects (_primary.dat files)
        self.write("VHDL_OBJ := ")
        for vhdl in fileset.filter(VHDLFile):
            #file compilation indicator (important: add _vhd ending)
            self.write(os.path.join(vhdl.library, vhdl.purename, "."+vhdl.purename+"_"+vhdl.extension()) + " \\\n")
        self.write('\n')

        self.write('LIBS := ')
        self.write(' '.join(libs))
        self.write('\n')
        #tell how to make libraries
        self.write('LIB_IND := ')
        self.write(' '.join([lib+"/."+lib for lib in libs]))
        self.write('\n')

        if top_module.manifest_dict["sim_pre_cmd"]:
            sim_pre_cmd = top_module.manifest_dict["sim_pre_cmd"]
        else:
            sim_pre_cmd = ''

        if top_module.manifest_dict["sim_post_cmd"]:
            sim_post_cmd = top_module.manifest_dict["sim_post_cmd"]
        else:
            sim_post_cmd = ''

        make_text_p2 = make_preambule_p2.substitute(sim_pre_cmd=sim_pre_cmd, sim_post_cmd=sim_post_cmd)
        self.writeln(make_text_p2)

        # ISim does not have a vmap command to insert additional libraries in
        #.ini file.
        for lib in libs:
            self.write(lib+"/."+lib+":\n")
            self.write(' '.join(["\t(mkdir", lib, "&&", "touch", lib+"/."+lib+" "]))
            #self.write(' '.join(["&&", "echo", "\""+lib+"="+lib+"/."+lib+"\" ", ">>", "xilinxsim.ini) "]))
            self.write(' '.join(["&&", "echo", "\""+lib+"="+lib+"\" ", ">>", "xilinxsim.ini) "]))
            self.write(' '.join(["||", "rm -rf", lib, "\n"]))
            self.write('\n')

            # Modify xilinxsim.ini file by including the extra local libraries
            #self.write(' '.join(["\t(echo """, lib+"="+lib+"/."+lib, ">>", "${XILINX_INI_PATH}/xilinxsim.ini"]))

        #rules for all _primary.dat files for sv
        #incdir = ""
        objs = []
        for vl in fileset.filter(VerilogFile):
            comp_obj = os.path.join(vl.library, vl.purename)
            objs.append(comp_obj)
            #self.write(os.path.join(vl.library, vl.purename, '.'+vl.purename+"_"+vl.extension())+': ')
            #self.writeln(".PHONY: " + os.path.join(comp_obj, '.'+vl.purename+"_"+vl.extension()))
            self.write(os.path.join(comp_obj, '.'+vl.purename+"_"+vl.extension())+': ')
            self.write(vl.rel_path() + ' ')
            self.writeln(' '.join([fname.rel_path() for fname in vl.depends_on]))
            self.write("\t\tvlogcomp -work "+vl.library+"=./"+vl.library)
            self.write(" $(VLOGCOMP_FLAGS) ")
            #if isinstance(vl, SVFile):
            #    self.write(" -sv ")
            #incdir = "-i "
            #incdir += " -i ".join(vl.include_dirs)
            #incdir += " "
            self.write(' -i ')
            self.write(' '.join(vl.include_dirs) + ' ')
            self.writeln(vl.vlog_opt+" $<")
            self.write("\t\t@mkdir -p $(dir $@)")
            self.writeln(" && touch $@ \n\n")
        self.write("\n")

        #list rules for all _primary.dat files for vhdl
        for vhdl in fileset.filter(VHDLFile):
            lib = vhdl.library
            purename = vhdl.purename
            comp_obj = os.path.join(lib, purename)
            objs.append(comp_obj)
            #each .dat depends on corresponding .vhd file and its dependencies
            #self.write(os.path.join(lib, purename, "."+purename+"_"+ vhdl.extension()) + ": "+ vhdl.rel_path()+" " + os.path.join(lib, purename, "."+purename) + '\n')
            #self.writeln(".PHONY: " + os.path.join(comp_obj, "."+purename+"_"+ vhdl.extension()))
            self.write(os.path.join(comp_obj, "."+purename+"_" + vhdl.extension()) + ": " + vhdl.rel_path()+" " + os.path.join(lib, purename, "."+purename) + '\n')
            self.writeln(' '.join(["\t\tvhpcomp $(VHPCOMP_FLAGS)", vhdl.vcom_opt, "-work", lib+"=./"+lib, "$< "]))
            self.writeln("\t\t@mkdir -p $(dir $@) && touch $@\n")
            self.writeln()
            # dependency meta-target. This rule just list the dependencies of the above file
            #if len(vhdl.depends_on) != 0:
            #self.writeln(".PHONY: " + os.path.join(lib, purename, "."+purename))
            # Touch the dependency file as well. In this way, "make" will recompile only what is needed (out of date)
            #if len(vhdl.depends_on) != 0:
            self.write(os.path.join(lib, purename, "."+purename) + ":")
            for dep_file in vhdl.depends_on:
                if dep_file in fileset:
                    name = dep_file.purename
                    self.write(" \\\n" + os.path.join(dep_file.library, name, "."+name + "_" + vhdl.extension()))
                else:
                    self.write(" \\\n" + os.path.join(dep_file.rel_path()))
            self.write('\n')
            self.writeln("\t\t@mkdir -p $(dir $@) && touch $@\n")


    # FIX. Make it more robust
    def __get_rid_of_isim_incdirs(self, vlog_opt):
        if not vlog_opt:
            vlog_opt = ""
        vlogs = vlog_opt.split(' ')
        ret = []
        skip = False
        for v in vlogs:
            if skip:
                skip = False
                continue

            if not v.startswith("-i"):
                ret.append(v)
            else:
                skip = True
        return ' '.join(ret)


    def __get_xilinxsim_ini_dir(self, env):
        if env["isim_path"]:
            xilinx_dir = str(os.path.join(env["isim_path"],"..",".."))
        else:
            logging.error("Cannot calculate xilinx tools base directory")
            quit()

        hdl_language = 'vhdl' #'verilog'

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


