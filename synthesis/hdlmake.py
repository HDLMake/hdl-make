#!/usr/bin/python2.7
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
from helper_classes import Manifest, ManifestParser
from fetch import *


def main():
#    print("Start");

    global_mod.t0 = time.time()

    parser = optparse.OptionParser()
    #disabled due to introducing a new parser class. Help msg printing is not ready yet.

    parser.add_option("--manifest-help", action="store_true",
    dest="manifest_help", help="print manifest file variables description")

    parser.add_option("-k", "--make", dest="make", action="store_true",
    default=None, help="Generate a Makefile (simulation/synthesis)")

    parser.add_option("-f", "--fetch", action="store_true", dest="fetch",
    help="fetch and/or update remote modules listed in Manifet")

    parser.add_option("-l", "--synthesize-locally", dest="local",
    action="store_true", help="perform a local synthesis")

    parser.add_option("-r", "--synthesize-remotelly", dest="remote",
    action="store_true", help="perform a remote synthesis")

    parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
    default="false", help="verbose mode")

    parser.add_option("--ipcore", dest="ipcore", action="store_true",
    default="false", help="generate a pseudo ip-core")

    parser.add_option("--nodel", dest="nodel", action="store_true",
    default="false", help="don't delete intermediate makefiles")

    parser.add_option("--synth-server", dest="synth_server",
    default=None, help="use given SERVER for remote synthesis", metavar="SERVER")

    parser.add_option("--synth-user", dest="synth_user",
    default=None, help="use given USER for remote synthesis", metavar="USER")

    parser.add_option("--py", dest="arbitrary_code",
    default="", help="add arbitrary code to all manifests' evaluation")

    (options, args) = parser.parse_args()
    global_mod.options = options

#    print("Parsed");

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
        p.vprint("LoadTopManifest");
        top_manifest = Manifest(path=os.path.abspath(file))
        global_mod.top_module = Module(manifest=top_manifest, parent=None, source="local", fetchto=".")

        global_mod.top_module.parse_manifest()
        global_mod.global_target = global_mod.top_module.target
        global_mod.top_module.fetch()
    else:
        p.echo("No manifest found. At least an empty one is needed")
        quit()

    global_mod.ssh = Connection(options.synth_user, options.synth_server)

    if global_mod.options.local == True:
        local_synthesis()
    elif global_mod.options.remote == True:
        remote_synthesis()
    elif global_mod.options.make == True:
        generate_makefile()

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
    from dep_solver import DependencySolver
    import depend
    solver = DependencySolver()

    tm = global_mod.top_module
    flist = tm.build_global_file_list();
    flist_sorted = solver.solve(flist);

    if(tm.target == "simulation"):
        depend.generate_modelsim_makefile(flist_sorted, tm)
    elif (tm.target == "xilinx"):
        generate_ise_project(flist_sorted, tm);
        generate_ise_makefile(tm)

def generate_ise_makefile(top_mod):
    filename = "Makefile"
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


all:		syn

clean:
		rm -f $(ISE_CRAP)
		rm -rf xst xlnx_auto_*_xdb iseconfig _xmsgs _ngo

mrproper:
\trm -f *.bit *.bin *.mcs

syn:
		echo "project open $(PROJECT)" > run.tcl
		echo "process run {Generate Programming File} -force rerun_all" >> run.tcl
		xtclsh run.tcl
"""
    f.write(mk_text);
    f.close()
				

def generate_ise_project(fileset, top_mod):
    from flow import ISEProject, ISEProjectProperty
    
    prj = ISEProject()
    prj.add_files(fileset.files)
    prj.add_libs(fileset.get_libs())

    prj.add_property(ISEProjectProperty("Device", top_mod.syn_device))
    prj.add_property(ISEProjectProperty("Device Family", "Spartan6"))
    prj.add_property(ISEProjectProperty("Speed Grade", top_mod.syn_grade))
    prj.add_property(ISEProjectProperty("Package", top_mod.syn_package))
#    prj.add_property(ISEProjectProperty("Implementation Top", "Architecture|"+top_mod.syn_top))
    prj.add_property(ISEProjectProperty("Implementation Top", "Architecture|"+top_mod.syn_top))
    prj.add_property(ISEProjectProperty("Manual Implementation Compile Order", "true"))
    prj.add_property(ISEProjectProperty("Auto Implementation Top", "false"))
    prj.add_property(ISEProjectProperty("Implementation Top Instance Path", "/"+top_mod.syn_top))
    prj.emit_xml(top_mod.syn_project)

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

def local_run_xilinx_flow(tm):
    f = open("run.tcl","w");
    f.write("project open " + tm.syn_project);
    f.write("process run {Generate Programming Files} -force rerun_all");
    f.close()
    os.system("xtclsh run.tcl");


def local_synthesis():
    tm = global_mod.top_module
    if tm.target == "xilinx":
        local_run_xilinx_flow(tm)
    else:
        p.echo("Target " + tm.target + " is not synthesizable")


def generate_list_makefile():
    pass

main()
