#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import re
import string
import global_mod
from msg import my_msg
from msg import v_msg

std_libs = ['ieee', 'altera_mf', 'cycloneiii', 'lpm', 'std', 'unisim']


def search_for_use(file):
    """
    Reads a file and looks for 'use' clause. For every 'use' with
    non-standard library a tuple (lib, file) is returned in a list.
    """
    f = open(file, "r")
    text = f.readlines()
    
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
            if string.lower(m.group(1)) in std_libs:
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
    text = f.readlines()
    
    ret = []
    package_pattern = re.compile("^[ \t]*package[ \t]+([^ \t]+)[ \t]+is[ \t]*$")
    for line in text:
        m = re.match(package_pattern, line)
        if m != None:
            ret.append(m.group(1))
    f.close()
    return ret
    
def generate_deps_for_modules(modules_paths):
    if not isinstance(modules_paths, list):
        modules_paths = [modules_paths]
        
    import pprint
    pp = pprint.PrettyPrinter(indent = 2)
    
    from hdlmake import search_for_manifest
    module_manifest_dict = {} 
    for module in modules_paths:
        module_manifest_dict[module] = search_for_manifest(module)
        
    from hdlmake import parse_manifest
    opt_map_dict = {}
    for module in module_manifest_dict.keys():
        if module_manifest_dict[module] != None:
            opt_map_dict[module] = parse_manifest(module_manifest_dict[module])
    
    module_files_dict = {}
    from hdlmake import make_list_of_files
    for module in modules_paths:
        module_files_dict[module] = make_list_of_files(module)
    all_files = [os.path.abspath(x) for k in module_files_dict for x in module_files_dict[k]]
    all_vhdl_files = [x for x in all_files if os.path.splitext(x)[1] == '.vhd']
    
    file_use_clause_dict = {}
    for file in all_vhdl_files:
        file_use_clause_dict[file] = search_for_use(file)
    
    package_file_dict = {}
    for file in all_vhdl_files:
        packages = search_for_package(file) #look for package definitions
        if len(packages) != 0: #if there are some packages in the file
            for package in packages:
                if package in package_file_dict:
                    my_msg("There might be a problem... Compilation unit " + package +
                    " has several instances:\n\t" + file + "\n\t" + package_file_dict[package])
                    package_file_dict[string.lower(package)] = [package_file_dict[string.lower(package)], file]#///////////////////////////////////////////////////
                package_file_dict[string.lower(package)] = file #map found package to scanned file
        file_basename = os.path.basename(file)
        file_purename = os.path.splitext(file_basename)[0]
        if file_purename in package_file_dict and package_file_dict[string.lower(file_purename)] != file:
            my_msg("There might be a problem... Compilation unit " + file_purename +
                " has several instances:\n\t" + file + "\n\t" + package_file_dict[file_purename])
        package_file_dict[string.lower(file_purename)] = file
    
    if global_mod.options.verbose == True:
        pp.pprint(package_file_dict)
    
    file_file_dict = {}
    for file in all_vhdl_files:
        file_units_list = file_use_clause_dict[file]
        for unit in file_units_list:
            if string.lower(unit[1]) in package_file_dict:
                if file in file_file_dict:
                    file_file_dict[file].append(package_file_dict[string.lower(unit[1])])
                else:
                    file_file_dict[file] = [package_file_dict[string.lower(unit[1])]]
            else:
                my_msg("Cannot resolve dependency: " + file + " depends on "
                    +"compilation unit " + str(unit) + ", which cannot be found")
    for file in all_vhdl_files:
        if file not in file_file_dict:
            file_file_dict[file] = []
    if global_mod.options.verbose == True:
        pp.pprint(file_file_dict)
    return file_file_dict
    
def generate_makefile(file_deps_dict):
    make_preambule_p1 = """## variables #############################
PWD := $(shell pwd)
WORK_NAME := work

MODELSIM_INI_PATH := /opt/modeltech

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
\t\trm -rf ./modelsim.ini $(LIBS) $(LIB_IND) $(WORK_NAME)
.PHONY: clean

"""
    pwd = os.getcwd()
    #open the file and write the above preambule (part 1)
    f = open("makefile", "w")
    f.write(make_preambule_p1)
    
    #list vhdl objects (_primary.dat files)
    f.write("VHDL_OBJ := ")
    for file in file_deps_dict:
        basename = os.path.basename(file)
        purename = os.path.splitext(basename)[0]
        f.write(pwd+'/'+'work'+'/'+purename+ "/_primary.dat"+" \\\n")
    f.write('\n')
    
    #tell hwo to make libraries
    f.write('LIB_IND := work/.work\n')
    f.write(make_preambule_p2)
    f.write("work/.work:\n")
    f.write("\t(vlib work && vmap -modelsimini "+pwd+"/modelsim.ini " +"work "+pwd+"/work"+") || rm -rf "+"work\n")
    f.write("\ttouch work/.work\n")
    f.write('\n')
   
    #list rules for all _primary.dat files

    for file in file_deps_dict:
        basename = os.path.basename(file)
        purename = os.path.splitext(basename)[0]
        #each .dat depends on corresponding .vhd file
        f.write(pwd+'/'+'work'+'/'+purename+"/_primary.dat: "+file+'\n')
        f.write('\t\tvcom $(VCOM_FLAGS) -work '
            +'work'+' '+file+'\n')
        f.write('\n')
        if len(file_deps_dict[file]) != 0:
            f.write(pwd+'/'+'work'+'/'+purename+"/_primary.dat:")
            for dep_file in file_deps_dict[file]:
                dep_file = os.path.splitext(os.path.basename(dep_file))[0]
                f.write(" \\\n"+pwd+'/'+'work'+'/'+dep_file+"/_primary.dat")
            f.write('\n\n')
   
    f.close()