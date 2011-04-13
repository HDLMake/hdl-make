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
from fetch import fetch_from_svn, fetch_from_git, parse_repo_url
import mnfst

def inject_files_into_ise(ise_file, files_list):
    ise = open(ise_file, "r")
    ise_lines = ise.readlines()

    file_template = '    '+ "<file xil_pn:name=\"{0}\" xil_pn:type=\"FILE_VHDL\"/>\n"
    files_pattern = re.compile('[ \t]*<files>[ \t]*')
    new_ise = []
    for line in ise_lines:
        new_ise.append(line)

        if re.match(files_pattern, line) != None:
            for file in files_list:
                new_ise.append(file_template.format(os.path.relpath(file)))
    new_ise_file = open(ise_file + ".new", "w")
    new_ise_file.write(''.join(new_ise))
    new_ise_file.close()

def check_address_length(module):
    p = module.popen("uname -a")
    p = p.readlines()
    if not len(p):
        p.echo("Checking address length failed")
        return None
    elif "i686" in p[0]:
        return 32
    elif "x86_64" in p[0]:
        return 64
    else:
        return None

def main():
    import depend
    global_mod.t0 = time.time()
    parser = optparse.OptionParser()
    parser.add_option("--manifest-help", action="store_true", dest="manifest_help",
    help="print manifest file variables description")
    parser.add_option("-k", "--make", dest="make", action="store_true", default=None, help="prepare makefile for simulation")
    parser.add_option("-f", "--fetch", action="store_true", dest="fetch", help="fetch files from modules listed in MANIFEST")
    parser.add_option("-l", "--synthesize-locally", dest="local", action="store_true", help="perform a local synthesis")
    parser.add_option("-r", "--synthesize-remotelly", dest="remote", action="store_true", help="perform a remote synthesis")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default="false", help="verbose mode")
    parser.add_option("--inject", dest="inject", action="store_true", default=None, help="inject file list into ise project")
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
    if os.path.exists("manifest.py"):
        global_mod.top_manifest = os.path.abspath("manifest.py")
    else:
        p.echo("No manifest found. At least an empty one is needed")
        quit()

    if global_mod.options.synth_server != None:
        global_mod.synth_server = global_mod.options.synth_server
    if global_mod.options.synth_user != None:
        global_mod.synth_user = global_mod.options.synth_user

    global_mod.opt_map = mnfst.parse_manifest(global_mod.top_manifest) 

    if global_mod.opt_map.fetchto != None:
        global_mod.fetchto = global_mod.opt_map.fetchto
    else:
        global_mod.fetchto = global_mod.hdlm_path

    if global_mod.options.tcl == None:
        if global_mod.opt_map.tcl == None: #option taken, but no tcl given -> find it
            tcl_pat = re.compile("^.*\.tcl$")
            for file in os.listdir("."): #try to find it in the current dir
                if re.match(tcl_pat, file):
                    global_mod.opt_map.tcl = file
                    break
    else:
        global_mod.opt_map.tcl = global_mod.options.tcl
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    if global_mod.options.manifest_help == True:
        parser = mnfst.init_manifest_parser()
        parser.print_help()
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    if global_mod.options.fetch == True:
        modules = mnfst.fetch_manifest(global_mod.top_manifest, global_mod.opt_map)
        p.vprint("Involved modules:")
        p.vpprint(modules)
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    if global_mod.options.local == True:
        if global_mod.opt_map.tcl == None:
            complain_tcl()
            quit()
        if not os.path.exists("/opt/Xilinx/" + global_mod.opt_map.ise):
            p.echo("The script can't find demanded ISE version: " + global_mod.opt_map.ise)
            quit()

        address_length = check_address_length(os)
        if address_length == 32 or address_length == None:
            path_ext = global_mod.ise_path_32[global_mod.opt_map.ise]
        else:
            p.echo("Don't know how to run settings script for ISE version: " + global_mod.opt_map.ise)
        results = os.popen("export PATH=$PATH:"+path_ext+" &&xtclsh " + global_mod.opt_map.tcl + " run_process")
        p.echo(results.readlines())
        quit()
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    if global_mod.options.remote == True:
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
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    if global_mod.options.make_list == True:
        import depend
        modules = path.make_list_of_modules(global_mod.top_manifest, global_mod.opt_map)

        p.vprint("Modules that will be taken into account in the makefile: " + str(modules))
        deps, libs = depend.generate_deps_for_vhdl_in_modules(modules)
        depend.generate_list_makefile(deps, libs)
        os.system("make -f " + global_mod.ise_list_makefile)
        os.remove(global_mod.ise_list_makefile)
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    if global_mod.options.make == True:
        import depend
        module_manifest_dict = path.make_list_of_modules(global_mod.top_manifest, global_mod.opt_map)
        p.vprint("Modules that will be taken into account in the makefile: ")
        p.vpprint(module_manifest_dict)

        deps, libs = depend.generate_deps_for_vhdl_in_modules(module_manifest_dict)
        depend.generate_makefile(deps, libs)
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    if global_mod.options.inject == True:
        if global_mod.options.ise_project == None:
            p.echo("You forgot to specify .xise file, didn't you?")
            quit()
        if not os.path.exists(global_mod.options.ise_project):
            p.echo("Given ise file doesn't exist")
            quit()

        import depend
        module_manifest_dict = path.make_list_of_modules(global_mod.top_manifest, global_mod.opt_map)
        p.vprint("Modules that will be taken into account in the makefile: ")
        p.vpprint(modules)

        module_files_dict = path.make_list_of_files(module_manifest_dict, file_type="vhd")
        p.vprint("List of used files")
        p.vpprint(module_files_dict)

        inject_files_into_ise(global_mod.options.ise_project, files)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if __name__ == "__main__":
    #global options' map for use in the entire script
    t0 = None
    global_mod.synth_user = "htsynth"
    global_mod.synth_server = "htsynth"
    global_mod.cwd = os.getcwd()
    #globa_mod.ssh = myssh.MySSH(global_mod.synth_user, global_mod.synth_server)
    main()
