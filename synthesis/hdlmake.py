#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import fileinput
import sys
import path
import path
import time
import os
from connection import Connection
import random
import string
import global_mod
import msg as p
import optparse
from module import Module
from helper_classes import Manifest, SourceFile, ManifestParser

def main():
    global_mod.t0 = time.time()
    parser = optparse.OptionParser()
    #disabled due to introducing a new parser class. Help msg printing is not ready yet.

    parser.add_option("--manifest-help", action="store_true",
    dest="manifest_help", help="print manifest file variables description")

    parser.add_option("-k", "--make", dest="make", action="store_true",
    default=None, help="prepare makefile for simulation")

    parser.add_option("-f", "--fetch", action="store_true", dest="fetch",
    help="fetch files from modules listed in MANIFEST")

    parser.add_option("--make-fetch", action="store_true", dest="make_fetch",
    help="generate makefile for fetching needed modules")

    parser.add_option("-l", "--synthesize-locally", dest="local",
    action="store_true", help="perform a local synthesis")

    parser.add_option("-r", "--synthesize-remotelly", dest="remote",
    action="store_true", help="perform a remote synthesis")

    parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
    default="false", help="verbose mode")

    parser.add_option("--ipcore", dest="ipcore", action="store_true",
    default="false", help="generate a pseudo ip-core")

    parser.add_option("--inject", dest="inject", action="store_true",
    default=None, help="inject file list into ise project")

    parser.add_option("--nodel", dest="nodel", action="store_true",
    default="false", help="don't delete intermediate makefiles")

    parser.add_option("--make-list", dest="make_list", action="store_true",
    default=None, help="make list of project files in ISE format")

    parser.add_option("--tcl-file", dest="tcl",
    help="specify a .tcl file used for synthesis with ISE")

    parser.add_option("--qpf-file", dest="qpf",
    help="specify a .qpf file used for synthesis with QPF")

    parser.add_option("--ise-file", dest="ise",
    help="specify .xise file for other actions", metavar="ISE")
 
    parser.add_option("--synth-server", dest="synth_server",
    default=None, help="use given SERVER for remote synthesis", metavar="SERVER")

    parser.add_option("--synth-user", dest="synth_user",
    default=None, help="use given USER for remote synthesis", metavar="USER")

    parser.add_option("--py", dest="arbitrary_code",
    default="", help="add arbitrary code to all manifests' evaluation")

    (options, args) = parser.parse_args()
    global_mod.options = options

    if options.manifest_help == True:
        ManifestParser().help()
        quit()
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
        global_mod.global_target = global_mod.top_module.target
    else:
        p.echo("No manifest found. At least an empty one is needed")
        quit()

    global_mod.ssh = Connection(options.synth_user, options.synth_server)

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
    depend.inject_files_into_ise(global_mod.options.ise_project, files)

def generate_makefile():
    import depend
    tm = global_mod.top_module
    vhdl_deps = tm.generate_deps_for_vhdl_in_modules()
    sv_files = tm.make_list_of_sv_files()
    #print sv_files
    #quit()
    depend.generate_makefile(vhdl_deps)

    #NOT YET TRANSFORMED INTO CLASSES
def remote_synthesis():
    ssh = global_mod.ssh
    tm = global_mod.top_module

    p.vprint("The program will be using ssh connection: "+str(ssh))
    if not ssh.is_good():
        p.echo("SSH connection failure. Remote host doesn't response.")
        quit()

    if not os.path.exists(tm.fetchto):
        p.echo("There are no modules fetched. Are you sure it's correct?")

    modules = global_mod.top_module.make_list_of_modules()

    files = [file for mod in modules for file in mod.files]
    dest_folder = ssh.transfer_files_forth(files, tm.name)

    ret = ssh.system("[ -e /opt/Xilinx/" + tm.ise + " ]")
    if ret == 1:
        p.echo("There is no " + tm.ise + " ISE version installed on the remote machine")
        quit()

    p.vprint("Checking address length at synthesis server")
    address_length = ssh.check_address_length()
    if address_length == 32 or address_length == None:
        path_ext = global_mod.ise_path_32[tm.ise]
    else:
        path_ext = global_mod.ise_path_64[tm.ise]
    cwd = os.getcwd()
    quit()
#### tu zmienic (jak Tomek rozczai)
    syn_cmd ="PATH=$PATH:"+path_ext+"&& cd "+dest_folder+cwd+"/"+os.path.dirname(global_mod.opt_map.tcl)
    syn_cmd += "&& xtclsh "+os.path.basename(global_mod.opt_map.tcl)+" run_process"
###
    p.vprint("Launching synthesis on " + str(ssh) + ": " + syn_cmd)
    ret = ssh.system(syn_cmd)
    if ret == 1:
        p.echo("Synthesis failed. Nothing will be transfered back")
        quit()

    cur_dir = os.path.basename(global_mod.cwd)
    os.chdir("..")
    ssh.transfer_files_back(dest_folder+global_mod.cwd)
    os.chdir(cur_dir)
    if global_mod.options.no_del != True:
        p.echo("Deleting synthesis folder")
        ssh.system('rm -rf ' + dest_folder)

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
    global_mod.cwd = os.getcwd()
    main()
