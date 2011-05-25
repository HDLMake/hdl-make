#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import string
import msg as p

class MakefileWriter(object):

    def generate_remote_synthesis_makefile(self, files, name, cwd, user, server, file=None):
        if files == None:
            import random
            name = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(8))
        if file== None:
            file = open("Makefile.remote","w")
        credentials_tmpl = "USER = {0}\nSERVER = {1}\nR_NAME= {2}\n"
        files_tmpl = "FILES = {0}"

        file.write(credentials_tmpl.format(user, server, name))
        file.write("CWD=$(shell pwd)\n")
        file.write("\n\n")
        file.write(files_tmpl.format(' \\\n'.join([str(s) for s in files])))
        file.write("\n\n")
        file.write("remote_synthesis: send do_synthesis send_back\n")
        file.write("send_back: do_synthesis\n")
        file.write("do_synthesis: send\n\n")

        mkdir_cmd = "ssh $(USER)@$(SERVER) 'mkdir -p $(R_NAME)'"
        rsync_cmd = "rsync -Rav $(FILES) $(USER)@$(SERVER):$(R_NAME)"
        send_cmd = "send:\n\t\t{0}\n\t\t{1}".format(mkdir_cmd, rsync_cmd)
        file.write(send_cmd)
        file.write("\n\n")

        tcl = "run.tcl"
        synthesis_cmd = "do_synthesis:\n\t\t"
        synthesis_cmd += "ssh $(USER)@$(SERVER) 'cd $(R_NAME)$(CWD) && xtclsh {1}'"
        file.write(synthesis_cmd.format(os.path.join(name, cwd), tcl))
        file.write("\n\n")
 
        send_back_cmd = "send_back: \n\t\tcd ..\n\t\trsync -av $(USER)@$(SERVER):$(R_NAME)$(CWD) .\n\t\tcd $(CWD)"
        file.write(send_back_cmd)
        file.write("\n\n")

        cln_cmd = "clean:\n\t\tssh $(USER)@$(SERVER) 'rm -rf $(R_NAME)'"
        file.write(cln_cmd)
        file.write("\n")
        file.close()

    def generate_ise_makefile(self, top_mod, file=None):
        if file == None:
            file = open("Makefile.ise","w")

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
        file.write(mk_text);
        file.close()

    def generate_fetch_makefile(self, modules_pool, file=None):
        import path
        rp = os.path.relpath
        if file == None:
            file = open("Makefile.fetch", "w")
        file.write("fetch: ")
        file.write(' \\\n'.join([m.basename()+"__fetch" for m in modules_pool if m.source in ["svn","git"]]))
        file.write("\n\n")

        for module in modules_pool:
            basename = module.basename()
            dir = os.path.join(module.fetchto, basename)
            if module.source == "svn":
                file.write(basename+"__fetch:\n")
                file.write("\t\t")
                file.write("PWD=$(shell pwd); ")
                file.write("cd " + rp(module.fetchto) + '; ')
                c = "svn checkout {0} {1};"
                if module.revision:
                    c.format(module.url, module.revision)
                else:
                    c.format(module.url, "")
                file.write(c)
                file.write("cd $(PWD) \n\n")

            elif module.source == "git":
                file.write(basename+"__fetch:\n")
                file.write("\t\t")
                file.write("PWD=$(shell pwd); ")
                file.write("cd " + rp(module.fetchto) + '; ')
                file.write("if [ -d " + basename + " ]; then cd " + basename + '; ')
                file.write("git pull; ")
                if module.revision:
                    file.write("git checkout " + module.revision +';')
                file.write("else git clone "+ module.url + '; fi; ')
                if module.revision:
                    file.write("git checkout " + module.revision + ';')
                file.write("cd $(PWD) \n\n")
        file.close()

#    def generate_pseudo_ipcore_makefile(self, file_deps_dict, filename="ipcore"):
#        import path
#        rp = os.path.relpath
#
#        f = open("Makefile.ipcore", "w")
#        f.write("file: create_a_file done\n")
#        f.write("create_a_file:\n\t\t@printf \"\" > " + filename + '\n')
#        f.write("file: ")
#        for file in file_deps_dict:
#            f.write(rp(file.path)+"__cat \\\n")
#        f.write("\n")
#        for file in file_deps_dict:
#            f.write(rp(file.path)+"__cat: ")
#            f.write(' '.join(rp(depfile.path)+"__cat" for depfile in file_deps_dict[file]))
#            f.write('\n')
#            f.write("\t\t@echo '-- " + file.name + "' >> " + filename + "\n")
#            f.write("\t\t@cat "+ rp(file.path) + " >> " + filename + "\n")
#            f.write("\t\t@echo \"\">> " +filename + "\n\n")
#
#        f.write("done:\n\t\t@echo Done.")

    def generate_modelsim_makefile(self, fileset, top_module, file=None):
        from time import gmtime, strftime
        from srcfile import VerilogFile, VHDLFile
        import path
        if file == None:
            file = open("Makefile.sim","w")

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

VCOM_FLAGS := -nologo -quiet -93 -modelsimini ./modelsim.ini """ + self.__emit_string(top_module.vcom_opt) + """
VSIM_FLAGS := """ + self.__emit_string(top_module.vsim_opt) + """
VLOG_FLAGS := -nologo -quiet -sv -modelsimini $(PWD)/modelsim.ini """ + self.__emit_string(top_module.vlog_opt) + """
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
        file.write(notices)
        file.write(make_preambule_p1)

        rp = os.path.relpath
        file.write("VERILOG_SRC := ")

        for vl in fileset.filter(VerilogFile):
            file.write(rp(vl.path) + " \\\n")
        file.write("\n")

        file.write("VERILOG_OBJ := ")
        for vl in fileset.filter(VerilogFile):
            file.write(os.path.join(vl.library, vl.purename, "."+vl.purename) + " \\\n")
        file.write('\n')

        libs = set(f.library for f in fileset.files)

        #list vhdl objects (_primary.dat files)
        file.write("VHDL_OBJ := ")
        for vhdl in fileset.filter(VHDLFile):
            file.write(os.path.join(vhdl.library, vhdl.purename,"."+vhdl.purename) + " \\\n")
        file.write('\n')

        file.write('LIBS := ')
        file.write(' '.join(libs))
        file.write('\n')
        #tell how to make libraries
        file.write('LIB_IND := ')
        file.write(' '.join([lib+"/."+lib for lib in libs]))
        file.write('\n')
        file.write(make_preambule_p2)

        vlo = top_module.vlog_opt
        vmo = top_module.vmap_opt
        for lib in libs:
            file.write(lib+"/."+lib+":\n")
            file.write(' '.join(["\t(vlib",  lib, "&&", "vmap", "-modelsimini modelsim.ini", 
            lib, "&&", "touch", lib+"/."+lib,")"]))

            file.write(' '.join(["||", "rm -rf", lib, "\n"]))
            file.write('\n')

        #rules for all _primary.dat files for sv
        for vl in fileset.filter(VerilogFile):
            file.write(os.path.join(vl.library, vl.purename, '.'+vl.purename)+': '+rp(vl.path)+"\n")
            file.write("\t\tvlog -work "+vl.library+" $(VLOG_FLAGS) +incdir+ "+os.path.dirname(vl.path)+" $<")
            file.write(" && mkdir -p "+os.path.join(vl.library+'/'+vl.purename) )
            file.write(" && touch "+ os.path.join(vl.library, vl.purename, '.'+vl.purename)+'\n')
        file.write("\n")

        #list rules for all _primary.dat files for vhdl
        vco = top_module.vcom_opt
        for vhdl in fileset.filter(VHDLFile):
            lib = vhdl.library
            basename = vhdl.name
            purename = vhdl.purename 
            #each .dat depends on corresponding .vhd file
            file.write(os.path.join(lib, purename, "."+purename) + ": "+rp(vhdl.path)+'\n')
            file.write(' '.join(["\t\tvcom $(VCOM_FLAGS)", vco, "-work", lib, rp(vhdl.path),
            "&&", "mkdir -p", os.path.join(lib, purename), "&&", "touch", os.path.join(lib, purename, '.'+ purename), '\n']))
            file.write('\n')
            if len(vhdl.dep_depends_on) != 0:
                file.write(os.path.join(lib, purename, "."+purename) +":")
                for dep_file in vhdl.dep_depends_on:
                    name = dep_file.purename
                    file.write(" \\\n"+ os.path.join(dep_file.library, name, "."+name))
                file.write('\n\n')

        file.close()

    def __emit_string(self, s):
        if not s:
            return ""
        else:
            return s

    def __modelsim_ini_path(self):
        vsim_path = os.popen("which vsim").read().strip()
        bin_path = os.path.dirname(vsim_path)
        return os.path.abspath(bin_path+"/../")
