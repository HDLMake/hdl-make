#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import fileinput
import sys
import path
import path
import time
import os
from connection import check_address_length
from connection import Connection
import random
import string
import global_mod
import msg as p
import optparse
from module import Module
from helper_classes import Manifest, SourceFile

def main():
    global_mod.t0 = time.time()
    parser = optparse.OptionParser()
    #disabled due to introducing a new parser class. Help msg printing is not ready yet.
    #parser.add_option("--manifest-help", action="store_true", dest="manifest_help",
    #help="print manifest file variables description")
    parser.add_option("-k", "--make", dest="make", action="store_true", default=None, help="prepare makefile for simulation")
    parser.add_option("-f", "--fetch", action="store_true", dest="fetch", help="fetch files from modules listed in MANIFEST")
    parser.add_option("--make-fetch", action="store_true", dest="make_fetch", help="generate makefile for fetching needed modules")
    parser.add_option("-l", "--synthesize-locally", dest="local", action="store_true", help="perform a local synthesis")
    parser.add_option("-r", "--synthesize-remotelly", dest="remote", action="store_true", help="perform a remote synthesis")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default="false", help="verbose mode")
    parser.add_option("--ipcore", dest="ipcore", action="store_true", default="false", help="generate a pseudo ip-core")
    parser.add_option("--inject", dest="inject", action="store_true", default=None, help="inject file list into ise project")
    parser.add_option("--nodel", dest="nodel", action="store_true", default="false", help="don't delete intermediate makefiles")
    parser.add_option("--make-list", dest="make_list", action="store_true", default=None, help="make list of project files in ISE format")
    parser.add_option("--tcl-file", dest="tcl", help="specify a .tcl file used for synthesis with ISE") 
    parser.add_option("--qpf-file", dest="qpf", help="specify a .qpf file used for synthesis with QPF")
    parser.add_option("--ise-file", dest="ise", help="specify .xise file for other actions", metavar="ISE")
    parser.add_option("--synth-server", dest="synth_server", default=None, help="use given SERVER for remote synthesis", metavar="SERVER")
    parser.add_option("--synth-user", dest="synth_user", default=None, help="use given USER for remote synthesis", metavar="USER")
    (global_mod.options, args) = parser.parse_args()

    # check if manifest is given in the command line
    # if yes, then use it
    # if no, the look for it in the current directory (python manifest has priority)  
    file = None
    if os.path.exists("manifest.py"):
        file = "manifest.py"
    elif os.path.exists("Manifest.py"):
        file = "Manifest.py"
    
    if file != None:
        top_manifest = Manifest(path=os.path.abspath(file))
        global_mod.top_module = Module(manifest=top_manifest, parent=None, source="local", fetchto=".")
        global_mod.top_module.parse_manifest()
    else:
        p.echo("No manifest found. At least an empty one is needed")
        quit()

    if global_mod.options.synth_server != None:
        global_mod.synth_server = global_mod.options.synth_server
    if global_mod.options.synth_user != None:
        global_mod.synth_user = global_mod.options.synth_user

    #if global_mod.options.tcl == None:
    #    if global_mod.opt_map.tcl == None: #option taken, but no tcl given -> find it
    #        tcl_pat = re.compile("^.*\.tcl$")
    #        for file in os.listdir("."): #try to find it in the current dir
    #            if re.match(tcl_pat, file):
    #                global_mod.opt_map.tcl = file
    #                break
    #else:
    #    global_mod.opt_map.tcl = global_mod.options.tcl

    #if global_mod.options.manifest_help == True:
    #    ManifestParser().print_help()
    if global_mod.options.fetch == True:
        fetch()
    elif global_mod.options.local == True:
        local_synthesis()
    elif global_mod.options.remote == True:
        remote_synthesis()
    elif global_mod.options.make_list == True:
        generate_list_makefile()
    elif global_mod.options.make == True:
        generate_makefile()
    elif global_mod.options.inject == True:
        inject_into_ise()
    elif global_mod.options.ipcore == True:
        generate_pseudo_ipcore()
    elif global_mod.options.make_fetch == True:
        generate_fetch_makefile()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
def generate_pseudo_ipcore():
    import depend
    tm = global_mod.top_module
    file_deps_dict = tm.generate_deps_for_vhdl_in_modules()
    depend.generate_pseudo_ipcore(file_deps_dict)

    if global_mod.options.nodel != True:
        os.remove("Makefile.ipcore")
    os.system("make -f Makefile.ipcore")

def fetch():
    modules = global_mod.top_module.fetch()
    p.vprint("Involved modules:")
    p.vprint([str(m) for m in modules])

def generate_fetch_makefile():
    import depend
    tm = global_mod.top_module
    modules = [tm]
    while len(modules) > 0:
        module = modules.pop()
        for repo_module in module.svn+module.git:
            if not repo_module.isfetched:
                p.echo("Module remains unfetched: " + str(repo_module) +
                ". Fetching must be done prior to makefile generation")
                return
            modules.append(repo_module)

    depend.generate_fetch_makefile(tm)

#NOT YET PORTED
def inject_into_ise():
    if global_mod.options.ise_project == None:
        p.echo("You forgot to specify .xise file, didn't you?")
        quit()
    if not os.path.exists(global_mod.options.ise_project):
        p.echo("Given ise file doesn't exist")
        quit()

    tm = global_mod.top_module
    module_files_dict = make_list_of_files(file_type="vhd")
    p.vprint("List of used files")
    p.vpprint(module_files_dict)

    depend.inject_files_into_ise(global_mod.options.ise_project, files)

def generate_makefile():
    import depend
    tm = global_mod.top_module
    vhdl_deps = tm.generate_deps_for_vhdl_in_modules()
    sv_files = tm.make_lsit_of
    depend.generate_makefile(vhdl_deps)

    #NOT YET TRANSFORMED INTO CLASSES
def remote_synthesis():
    if global_mod.opt_map.tcl == None: #option not taken but mandatory
        p.echo("For Xilinx synthesis a .tcl file in the top module is required")
        quit()
    if not os.path.exists(global_mod.opt_map.tcl):
        p.echo("Given .tcl doesn't exist: " + global_mod.opt_map.tcl)
        quit()
    p.vprint("The program will be using ssh connection: "+global_mod.synth_user+"@"+global_mod.synth_server)
    global_mod.ssh = Connection(global_mod.synth_user, global_mod.synth_server)

    if not global_mod.ssh.is_good():
        p.echo("SSH connection failure.")
        quit()

    if not os.path.exists(global_mod.fetchto):
        p.echo("There are no modules fetched. Are you sure it's correct?")

    module_manifest_dict = path.make_list_of_modules(global_mod.top_manifest, global_mod.opt_map)
    p.vprint ("Modules: ")
    p.vpprint(module_manifest_dict)

    module_files_dict = path.make_list_of_files(module_manifest_dict)
    files = []
    for module in module_files_dict:
        files.extend(module_files_dict[module])

    p.vprint("Files that will be transfered")
    p.vpprint(files)
    dest_folder = global_mod.ssh.transfer_files_forth(files, global_mod.opt_map.name)

    ret = global_mod.ssh.system("[ -e /opt/Xilinx/"+global_mod.opt_map.ise+" ]")
    if ret == 1:
        p.echo("There is no "+global_mod.opt_map.ise+" ISE version installed on the remote machine")
        quit()

    p.vprint("Checking address length at synthesis server")
    address_length = check_address_length(global_mod.ssh)
    if address_length == 32 or address_length == None:
        path_ext = global_mod.ise_path_32[global_mod.opt_map.ise]
    else:
        path_ext = global_mod.ise_path_64[global_mod.opt_map.ise]

    syn_cmd ="PATH=$PATH:"+path_ext+"&& cd "+dest_folder+global_mod.cwd+"/"+os.path.dirname(global_mod.opt_map.tcl)
    syn_cmd += "&& xtclsh "+os.path.basename(global_mod.opt_map.tcl)+" run_process"

    p.vprint("Launching synthesis on " + global_mod.synth_server + ": " + syn_cmd)
    ret = global_mod.ssh.system(syn_cmd)
    if ret == 1:
        p.echo("Synthesis failed. Nothing will be transfered back")
        quit()

    cur_dir = os.path.basename(global_mod.cwd)
    os.chdir("..")
    global_mod.ssh.transfer_files_back(dest_folder+global_mod.cwd)
    os.chdir(cur_dir)
    if global_mod.options.no_del != True:
        p.echo("Deleting synthesis folder")
        global_mod.ssh.system('rm -rf ' + dest_folder)

def local_synthesis():
    if global_mod.options.tcl == None:
        p.echo("No .tcl file found. Exiting")
        quit()
    ise = global_mod.top_module.ise
    tcl = global_mod.options.tcl
    if not os.path.exists("/opt/Xilinx/" + ise):
        p.echo("The script can't find demanded ISE version: " + ise)
        quit()

    address_length = check_address_length(os)
    if address_length == 32 or address_length == None:
        path_ext = global_mod.ise_path_32[ise]
    else:
        p.echo("Don't know how to run settings script for ISE version: " + ise)
    results = os.popen("export PATH=$PATH:"+path_ext+" && xtclsh " + tcl + " run_process")
    p.echo(results.readlines())
    quit()

def generate_list_makefile():
    import depend
    tm = global_mod.top_module
    deps = tm.generate_deps_for_vhdl_in_modules()
    depend.generate_list_makefile(deps)
    os.system("make -f Makefile.list")

    if global_mod.options.nodel != True:
        os.remove("Makefile.list")

if __name__ == "__main__":
    #global options' map for use in the entire script
    t0 = None
    global_mod.synth_user = "htsynth"
    global_mod.synth_server = "htsynth"
    global_mod.cwd = os.getcwd()
    #globa_mod.ssh = myssh.MySSH(global_mod.synth_user, global_mod.synth_server)
    main()
