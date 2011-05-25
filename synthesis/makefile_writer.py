#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import re
import string
import global_mod
import msg as p
from srcfile import *


class MakefileWriter(object):

    def generate_remote_synthesis_makefile(self, files, name, cwd, user, server, filename=None):
        if files == None:
            import random
            name = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(8))
        if filename == None:
            filename = "Makefile.remote"
        f=open(filename, "w")
        credentials_tmpl = "USER = {0}\nSERVER = {1}\nR_NAME= {2}\n"
        files_tmpl = "FILES = {0}"

        f.write(credentials_tmpl.format(user, server, name))
        f.write("CWD=$(shell pwd)\n")
        f.write("\n\n")
        f.write(files_tmpl.format(' \\\n'.join([str(s) for s in files])))
        f.write("\n\n")
        f.write("remote_synthesis: send do_synthesis send_back\n")
        f.write("send_back: do_synthesis\n")
        f.write("do_synthesis: send\n\n")

        mkdir_cmd = "ssh $(USER)@$(SERVER) 'mkdir -p $(R_NAME)'"
        rsync_cmd = "rsync -Rav $(FILES) $(USER)@$(SERVER):$(R_NAME)"
        send_cmd = "send:\n\t\t{0}\n\t\t{1}".format(mkdir_cmd, rsync_cmd)
        f.write(send_cmd)
        f.write("\n\n")

        tcl = "run.tcl"
        synthesis_cmd = "do_synthesis:\n\t\t"
        synthesis_cmd += "ssh $(USER)@$(SERVER) 'cd $(R_NAME)$(CWD) && xtclsh {1}'"
        f.write(synthesis_cmd.format(os.path.join(name, cwd), tcl))
        f.write("\n\n")
 
        send_back_cmd = "send_back: \n\t\tcd ..\n\t\trsync -av $(USER)@$(SERVER):$(R_NAME)$(CWD) .\n\t\tcd $(CWD)"
        f.write(send_back_cmd)
        f.write("\n\n")

        cln_cmd = "clean:\n\t\tssh $(USER)@$(SERVER) 'rm -rf $(R_NAME)'"
        f.write(cln_cmd)
        f.write("\n")

    def generate_ise_makefile(self, top_mod, filename=None):
        if filename == None:
            filename = "Makefile.ise"
        f=open(filename,"w");

        mk_text = """
PROJECT=""" + top_mod.syn_project + """
ISE_CRAP = \
*.bgn \
*.html \
*.tcl \
*.bld \
*.cmd_log \
*.drc \
*.lso \
*.ncd \
*.ngc \
*.ngd \
*.ngr \
*.pad \
*.par \
*.pcf \
*.prj \
*.ptwx \
*.stx \
*.syr \
*.twr \
*.twx \
*.gise \
*.unroutes \
*.ut \
*.xpi \
*.xst \
*_bitgen.xwbt \
*_envsettings.html \
*_guide.ncd \
*_map.map \
*_map.mrp \
*_map.ncd \
*_map.ngm \
*_map.xrpt \
*_ngdbuild.xrpt \
*_pad.csv \
*_pad.txt \
*_par.xrpt \
*_summary.html \
*_summary.xml \
*_usage.xml \
*_xst.xrpt \
usage_statistics_webtalk.html \
webtalk.log \
webtalk_pn.xml \
run.tcl

syn:
\t\techo "project open $(PROJECT)" > run.tcl

clean:
\t\trm -f $(ISE_CRAP)
\t\trm -rf xst xlnx_auto_*_xdb iseconfig _xmsgs _ngo
    
mrproper:
\trm -f *.bit *.bin *.mcs
    
\t\techo "process run {Generate Programming File} -force rerun_all" >> run.tcl
\t\txtclsh run.tcl
        """
        f.write(mk_text);
        f.close()

    def generate_fetch_makefile(self, modules_pool):
        import path
        rp = os.path.relpath

        f = open("Makefile.fetch", "w")
        f.write("fetch: ")
        f.write(' \\\n'.join([m.basename()+"__fetch" for m in modules_pool if m.source in ["svn","git"]]))
        f.write("\n\n")

        for module in modules_pool:
            basename = module.basename()
            dir = os.path.join(module.fetchto, basename)
            if module.source == "svn":
                f.write(basename+"__fetch:\n")
                f.write("\t\t")
                f.write("PWD=$(shell pwd); ")
                f.write("cd " + rp(module.fetchto) + '; ')
                c = "svn checkout {0} {1};"
                if module.revision:
                    c.format(module.url, module.revision)
                else:
                    c.format(module.url, "")
                f.write(c)
                f.write("cd $(PWD) \n\n")

            elif module.source == "git":
                f.write(basename+"__fetch:\n")
                f.write("\t\t")
                f.write("PWD=$(shell pwd); ")
                f.write("cd " + rp(module.fetchto) + '; ')
                f.write("if [ -d " + basename + " ]; then cd " + basename + '; ')
                f.write("git pull; ")
                if module.revision:
                    f.write("git checkout " + module.revision +';')
                f.write("else git clone "+ module.url + '; fi; ')
                if module.revision:
                    f.write("git checkout " + module.revision + ';')
                f.write("cd $(PWD) \n\n")
        f.close()

    def generate_pseudo_ipcore_makefile(self, file_deps_dict, filename="ipcore"):
        import path
        rp = os.path.relpath

        f = open("Makefile.ipcore", "w")
        f.write("file: create_a_file done\n")
        f.write("create_a_file:\n\t\t@printf \"\" > " + filename + '\n')
        f.write("file: ")
        for file in file_deps_dict:
            f.write(rp(file.path)+"__cat \\\n")
        f.write("\n")
        for file in file_deps_dict:
            f.write(rp(file.path)+"__cat: ")
            f.write(' '.join(rp(depfile.path)+"__cat" for depfile in file_deps_dict[file]))
            f.write('\n')
            f.write("\t\t@echo '-- " + file.name + "' >> " + filename + "\n")
            f.write("\t\t@cat "+ rp(file.path) + " >> " + filename + "\n")
            f.write("\t\t@echo \"\">> " +filename + "\n\n")

        f.write("done:\n\t\t@echo Done.")

    def __emit_string(self, s):
        if not s:
            return ""
        else:
            return s

    def __modelsim_ini_path(self):
        vsim_path = os.popen("which vsim").read().strip()
        bin_path = os.path.dirname(vsim_path)
        return os.path.abspath(bin_path+"/../")

    def generate_modelsim_makefile(self, fileset, module, filename=None):
        from time import gmtime, strftime
        import path
        #from path import relpath as rp
        if filename == None:
            filename = "Makefile.sim"
        date = strftime("%a, %d %b %Y %H:%M:%S", gmtime())
        notices = """#######################################################################
#   This makefile has been automatically generated by hdl-make 
#   on """ + date + """
#######################################################################
"""

        make_preambule_p1 = """## variables #############################
PWD := $(shell pwd)
WORK_NAME := work

MODELSIM_INI_PATH := """ + self.__modelsim_ini_path() + """

VCOM_FLAGS := -nologo -quiet -93 -modelsimini ./modelsim.ini """ + self.__emit_string(module.vcom_opt) + """
VSIM_FLAGS := """ + self.__emit_string(module.vsim_opt) + """
VLOG_FLAGS := -nologo -quiet -sv -modelsimini $(PWD)/modelsim.ini """ + self.__emit_string(module.vlog_opt) + """
""" 
        make_preambule_p2 = """## rules #################################
sim: modelsim.ini $(LIB_IND) $(VERILOG_OBJ) $(VHDL_OBJ)
$(VERILOG_OBJ): $(VHDL_OBJ) 
$(VHDL_OBJ): $(LIB_IND) modelsim.ini

modelsim.ini: $(MODELSIM_INI_PATH)/modelsim.ini
\t\tcp $< .
clean:
\t\trm -rf ./modelsim.ini $(LIBS) $(WORK_NAME)
.PHONY: clean

"""
        #open the file and write the above preambule (part 1)
        f = open(filename, "w")
        f.write(notices)
        f.write(make_preambule_p1)

        rp = os.path.relpath
        f.write("VERILOG_SRC := ")

        for file in fileset.filter(VerilogFile):
            f.write(rp(file.path) + " \\\n")
        f.write("\n")

        f.write("VERILOG_OBJ := ")
        for file in fileset.filter(VerilogFile):
            f.write(os.path.join(file.library, file.purename, "."+file.purename) + " \\\n")
        f.write('\n')

        libs = set(file.library for file in fileset.files)

        #list vhdl objects (_primary.dat files)
        f.write("VHDL_OBJ := ")
        for file in fileset.filter(VHDLFile):
            f.write(os.path.join(file.library, file.purename,"."+file.purename) + " \\\n")
        f.write('\n')

        f.write('LIBS := ')
        f.write(' '.join(libs))
        f.write('\n')
        #tell how to make libraries
        f.write('LIB_IND := ')
        f.write(' '.join([lib+"/."+lib for lib in libs]))
        f.write('\n')
        f.write(make_preambule_p2)

        vlo = global_mod.top_module.vlog_opt
        vmo = global_mod.top_module.vmap_opt
        for lib in libs:
            f.write(lib+"/."+lib+":\n")
            f.write(' '.join(["\t(vlib",  lib, "&&", "vmap", "-modelsimini modelsim.ini", 
            lib, "&&", "touch", lib+"/."+lib,")"]))

            f.write(' '.join(["||", "rm -rf", lib, "\n"]))
            f.write('\n')

        #rules for all _primary.dat files for sv
        for file in fileset.filter(VerilogFile):
            f.write(os.path.join(file.library, file.purename, '.'+file.purename)+': '+rp(file.path)+"\n")
            f.write("\t\tvlog -work "+file.library+" $(VLOG_FLAGS) +incdir+ "+os.path.dirname(file.path)+" $<")
            f.write(" && mkdir -p "+os.path.join(file.library+'/'+file.purename) )
            f.write(" && touch "+ os.path.join(file.library, file.purename, '.'+file.purename)+'\n')
        f.write("\n")

        #list rules for all _primary.dat files for vhdl
        vco = global_mod.top_module.vcom_opt
        for file in fileset.filter(VHDLFile):
            lib = file.library
            basename = file.name
            purename = file.purename 
            #each .dat depends on corresponding .vhd file
            f.write(os.path.join(lib, purename, "."+purename) + ": "+rp(file.path)+'\n')
            f.write(' '.join(["\t\tvcom $(VCOM_FLAGS)", vco, "-work", lib, rp(file.path),
            "&&", "mkdir -p", os.path.join(lib, purename), "&&", "touch", os.path.join(lib, purename, '.'+ purename), '\n']))
            f.write('\n')
            if len(file.dep_depends_on) != 0:
                f.write(os.path.join(lib, purename, "."+purename) +":")
                for dep_file in file.dep_depends_on:
                    name = dep_file.purename
                    f.write(" \\\n"+ os.path.join(dep_file.library, name, "."+name))
                f.write('\n\n')

        f.close()
