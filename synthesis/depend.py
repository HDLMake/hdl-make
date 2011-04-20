#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import re
import string
import global_mod
import msg as p



def try_utf8(data):
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
            return None

def search_for_use(file):
    """
    Reads a file and looks for 'use' clause. For every 'use' with
    non-standard library a tuple (lib, file) is returned in a list.
    """
    f = open(file, "r")
    try:
        text = f.readlines()
    except UnicodeDecodeError:
        return []

    ret = []
    use_pattern = re.compile("^[ \t]*use[ \t]+([^; ]+)[ \t]*;.*$")
    lib_pattern = re.compile("([^.]+)\.([^.]+)\.all")

    use_lines = []
    for line in text:
        m = re.match(use_pattern, line)
        if m != None:
            use_lines.append(m.group(1))
    for line in use_lines:
        m = re.match(lib_pattern, line)
        if m != None:
            if (m.group(1)).lower() in std_libs:
                continue
            ret.append((m.group(1),m.group(2)))
    f.close()
    return ret

def search_for_package(file):
    """
    Reads a file and looks for package clase. Returns list of packages' names
    from the file
    """
    f = open(file, "r")
    try:
        text = f.readlines()
    except UnicodeDecodeError:
        return []

    ret = []
    package_pattern = re.compile("^[ \t]*package[ \t]+([^ \t]+)[ \t]+is[ \t]*$")
    for line in text:
        m = re.match(package_pattern, line)
        if m != None:
            ret.append(m.group(1))
    f.close()
    return ret

def generate_deps_for_sv_files(files):
    def search_for_sv_include(file):
        f = open(file,"r")
        text = f.readlines()

        ret = []
        package_pattern = re.compile("^[ \t]*`include[ \t]+\"([^ \t]+)\"[ \t]*$")
        for line in text:
            m = re.match(package_pattern, line)
            if m != None:
                ret.append(m.group(1))
        f.close()
        return ret

    if not isinstance(files,list):
        files = [files]
    file_files_dict = {}
    for file in files:
        file_files_dict[file] = search_for_sv_include(file)
    return file_files_dict

def modelsim_ini_path():
    vsim_path = os.popen("which vsim").read().strip()
    bin_path = os.path.dirname(vsim_path)
    return os.path.abspath(bin_path+"/../")

def inject_files_into_ise(ise_file, files_list):
    ise = open(ise_file, "r")
    ise_lines = ise.readlines()
    file_template = '    '+ "<file xil_pn:name=\"{0}\" xil_pn:type=\"file_vhdl\"/>\n"
    files_pattern = re.compile('[ \t]*<files>[ \t]*')
    new_ise = []
    for line in ise_lines:
        new_ise.append(line)
        if re.match(files_pattern, line) != none:
            for file in files_list:
                new_ise.append(file_template.format(os.path.relpath(file)))

    new_ise_file = open(ise_file + ".new", "w")
    new_ise_file.write(''.join(new_ise))
    new_ise_file.close()

def generate_fetch_makefile(top_module):
    import path
    rp = os.path.relpath

    f = open("Makefile.fetch", "w")

    f.write("fetch: ")
    for m in top_module.svn:
        basename = path.url_basename(m.url)
        f.write(basename+"__fetch \n")
    for m in top_module.git:
        basename = path.url_basename(m.url)
        f.write(basename+"__fetch \n")

    f.write("\n")
    for m in top_module.svn:
        basename = path.url_basename(m.url)
        dir = os.path.join(m.fetchto, basename)
        f.write(basename+"__fetch:\n")
        f.write("\t\t")
        f.write("PWD=$(shell pwd) ; ")
        f.write("cd " + rp(m.fetchto) + ' ; ')
        f.write("svn checkout "+ m.url + ' ; ')
        f.write("cd $(PWD) \n\n")

    for m in top_module.git:
        basename = path.url_basename(m.url)
        dir = os.path.join(m.fetchto, basename)
        f.write(basename+"__fetch:\n")
        f.write("\t\t")
        f.write("PWD=$(shell pwd) ; ")
        f.write("cd " + rp(m.fetchto) + ' ; ')
        f.write("git clone "+ m.url + ' ; ')
        f.write("cd $(PWD) \n\n")
    f.close()

def generate_pseudo_ipcore(file_deps_dict, filename="ipcore"):
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

def generate_list_makefile(file_deps_dict, filename="Makefile.list"):
    import path

    rp = os.path.relpath
    f = open(filename, "w")
    f.write("file: create_a_file done\n")
    f.write("create_a_file:\n\t\t@printf \"\" > ise_list \n")
    f.write("file: ")
    for file in file_deps_dict:
        f.write(rp(file.path)+"__print \\\n")
    f.write("\n")
    for file in file_deps_dict:
        f.write(rp(file.path)+"__print: ")
        f.write(' '.join( rp(depfile.path)+"__print" for depfile in file_deps_dict[file]))
        f.write('\n')
        f.write("\t\t@echo \'"+file.library+';'+rp(file.path)+"\' >> ise_list\n\n")
    f.write("done:\n\t\t@echo Done.")

def generate_makefile(file_deps_dict, filename="Makefile"):
    from time import gmtime, strftime
    import path
    #from path import relpath as rp
    date = strftime("%a, %d %b %Y %H:%M:%S", gmtime())
    notices = """#######################################################################
#   This makefile has been automatically generated by hdl-make 
#   on """ + date + """
#######################################################################

"""
    make_preambule_p1 = """## variables #############################
PWD := $(shell pwd)
WORK_NAME := work

MODELSIM_INI_PATH := """ + modelsim_ini_path() + """

VCOM_FLAGS := -nologo -quiet -93 -modelsimini ./modelsim.ini
VSIM_FLAGS := -voptargs="+acc"
VLOG_FLAGS := -nologo -quiet -sv -modelsimini $(PWD)/modelsim.ini

#VHDL_OBJ is defined below
SV_SRC := $(wildcard $(PWD)/*.sv)
SV_OBJ := $(foreach svfile, $(SV_SRC), work/$(patsubst %.sv,%/_primary.dat,$(notdir $(svfile))))
"""
    make_preambule_p2 = """## rules #################################
all: modelsim.ini $(LIB_IND) $(SV_OBJ) $(VHDL_OBJ)
$(SV_OBJ): $(VHDL_OBJ) 
$(VHDL_OBJ): $(LIB_IND) modelsim.ini

work/%/_primary.dat: %.sv
\t\tvlog -work work $(VLOG_FLAGS) $<
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

    libs = set(file.library for file in list(file_deps_dict.keys()))
    #list vhdl objects (_primary.dat files)
    f.write("VHDL_OBJ := ")
    for file in file_deps_dict:
        f.write(file.library+'/'+file.purename+ "/."+file.purename+" \\\n")
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
        f.write(' '.join(["\t(vlib", vlo, lib, "&&", "vmap", vmo, "-modelsimini modelsim.ini", 
        lib, "&&", "touch", lib+"/."+lib,")"]))

        f.write(' '.join(["||", "rm -rf", lib, "\n"]))
        f.write('\n')

    #list rules for all _primary.dat files
    rp = os.path.relpath
    vco = global_mod.top_module.vcom_opt
    for file in file_deps_dict:
        lib = file.library
        basename = file.name
        purename = file.purename 
        #each .dat depends on corresponding .vhd file
        f.write(os.path.join(lib, purename, "."+purename) + ": "+rp(file.path)+'\n')
        f.write(' '.join(["\t\tvcom $(VCOM_FLAGS)", vco, "-work", lib, rp(file.path),
        "&&", "mkdir -p", os.path.join(lib, purename), "&&", "touch", os.path.join(lib, purename, '.'+ purename), '\n']))
        f.write('\n')
        if len(file_deps_dict[file]) != 0:
            f.write(os.path.join(lib, purename, "."+purename) +":")
            for dep_file in file_deps_dict[file]:
                name = dep_file.purename
                f.write(" \\\n"+ os.path.join(dep_file.library, name, "."+name))
            f.write('\n\n')

    f.close()