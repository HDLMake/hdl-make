#!/usr/bin/python
# -*- coding: utf-8 -*-

import cfgparse
import re
import fileinput
import sys
from path import make_list_of_files
import path
import time
import os
from connection import Connection
import random
import string
import global_mod
import msg as p
from optparse import OptionParser
from fetch import fetch_from_local, fetch_from_svn, fetch_from_git

def complain_tcl():
    print "For Xilinx synthesis a tcl file in the top module is required"


def parse_repo_url(url) :
    """
    Check if link to a repo seems to be correct
    """
    url_pat = re.compile("[ \t]*([^ \t]+)[ \t]*(@[ \t]*(.+))?[ \t]*")
    url_match = re.match(url_pat, url)
    
    if url_match == None:
        print "Skipping"
        raise RuntimeError("Not a correct repo url: " + url)
    if url_match.group(3) != None: #there is a revision given 
        ret = (url_match.group(1), url_match.group(3))
    else:
        ret = url_match.group(1)
    return ret
    


def check_module_and_append(list, module):
    """
    Appends a module to the list if it doesn't belong to it. If it is already there, complain
    """
    if list.count(module) != 0:
        print "Module " + module + " has been previously defined: ommiting"
        return 1 
    for i in list:
        if os.path.basename(i) == os.path.basename(module):
            print "Module " + module + " has the same name as " + i + " :ommiting"
            return 1
    list.append(module)
    return 0
    
def parse_manifest(manifest_file):
    
    def make_list(sth):
        if sth != None:
            if not isinstance(sth, (list,tuple)):
                sth = [sth]
        else:
            sth = []
        return sth
        
    manifest_path = os.path.dirname(manifest_file)
    
    manifest_parser = cfgparse.ConfigParser(allow_py = True)
    manifest_parser.add_option('root', default=None)
    manifest_parser.add_option('name', default=None)
    manifest_parser.add_option('tcl', default=None)
    manifest_parser.add_option('ise', default=None)
    manifest_parser.add_option('modules', dest="svn", keys="svn", default=None)
    manifest_parser.add_option('modules', dest="git", keys="git", default=None)
    manifest_parser.add_option('modules', dest="local", keys="local", default=None)
    manifest_parser.add_option('library', dest="library", default="work")
    manifest_parser.add_option('rtl', default=None)
    manifest_parser.add_option('files', default=None)
    manifest_parser.add_file(manifest_file)
    
    #Take configuration parser from the global namespace
    opt_map = manifest_parser.parse()
    
    if opt_map.root == None:
        opt_map.root = "."
        
    if opt_map.rtl == None:
        opt_map.rtl = ["."]
    elif not isinstance (opt_map.rtl, list):
        opt_map.rtl = [opt_map.rtl]

    if opt_map.ise == None:
        opt_map.ise = "13.1"
        
    opt_map.local = make_list(opt_map.local) 
    for i in opt_map.local:
        if path.is_abs_path(i):
            p.echo(sys.argv[0] + " accepts relative paths only: " + i)
            quit()
    opt_map.local = [path.rel2abs(x, manifest_path) for x in opt_map.local]

    opt_map.svn = make_list(opt_map.svn)
    opt_map.git = make_list(opt_map.git)
    opt_map.files = make_list(opt_map.files)
    return opt_map
 

def convert_xise(xise):
    if not os.path.exists(xise):
        p.echo("Given .xise file does not exist:" + xise)
        quit()
        
    modules = ["."]
    modules.append(global_mod.hdlm_path)
    files = make_list_of_files(modules)
    
    ise = open(xise, "r")
    ise_lines = [x.strip() for x in ise.readlines()]
    
    new_ise = []
    file_pattern = re.compile('([ \t]*<file xil_pn:name=")([^"]+)(".*>)')
    #print ise_lines
    new_ise = []
    for line in ise_lines:
        m = re.match(file_pattern, line)
        if m != None:
            filename = m.group(2)
            file_basename = path.url_basename(m.group(2))
            found = False
            for file in files:
                if file_basename in file:
                    found = True
                    new_ise.append(m.group(1) + path.path(os.path.abspath("."), file) + m.group(3))
                    break
            if found == False:
                p.echo("Not found proper file for " + filename)
                new_ise.append(line)
        else:
            new_ise.append(line + "\n")
    
    new_ise_file = open(xise + ".new", "w")
    
def search_for_manifest(search_path):
    """
    Look for manifest in the given folder ans subfolders
    """
    cmd = "find -H " + search_path + " -name manifest.py"
    p.vprint(cmd)
    files = os.popen(cmd).readlines()
    
    if len(files) == 0:
        p.vprint("No manifest found in: " + search_path)
        return None
    elif len(files) > 1:
        p.echo("Too many manifests in" + search_path + ": " + str(files))
        return files[0].strip()
        
    p.echo("Found manifest: " + os.path.abspath(files[0]).strip())
    return os.path.abspath(files[0].strip())     
                
def check_address_length(module):
    p = module.popen("uname -a")
    p = p.readlines()
    if "i686" in p[0]:
        return 32
    elif "x86_64" in p[0]:
        return 64
    else:
        return None
        
    
def main():
    # # # # # # #
    import depend
    global_mod.t0 = time.time()
    parser = OptionParser()
    parser.add_option("-f", "--fetch", action="store_true", dest="fetch", help="fetch files from modules listed in MANIFEST")
    parser.add_option("-c", "--clean", action="store_true", dest="clean", help="clean the mess made by me")
    parser.add_option("-l", "--synthesize-locally", dest="local", action="store_true", help="perform a local synthesis")
    parser.add_option("-r", "--synthesize-remotelly", dest="remote", action="store_true", help="perform a remote synthesis")
    parser.add_option("-t", "--tcl-file", dest="tcl", help="specify a TCL file used for synthesis") 
    parser.add_option("-m", "--manifest", dest="manifest", default=None, help="use given MANIFEST in all operations", metavar="MANIFEST")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default="false", help="verbose mode")
    parser.add_option("-k", "--do-make", dest="make", action="store_true", default=None, help="prepare makefile for simulation")
    parser.add_option("-o", "--convert-xise", dest="xise", default=None, help="convert paths in the given XISE_FILE", metavar="XISE_FILE")
    parser.add_option("-s", "--synth-server", dest="synth_server", default=None, help="use given SERVER for remote synthesis", metavar="SERVER")
    parser.add_option("-u", "--synth-user", dest="synth_user", default=None, help="use given USER for remote synthesis", metavar="USER")
    parser.add_option("--no-del", dest="no_del", default=None, help="do not delete catalog after remote synthesis")
    (global_mod.options, args) = parser.parse_args()
    
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #Check if any option was selected
    if global_mod.options.local == global_mod.options.fetch == global_mod.options.remote == global_mod.options.make == global_mod.options.clean == None:
        import sys
        p.echo("Are you sure you didn't forget to specify an option? At least one?")
        p.echo("Maybe you should try " + sys.argv[0] + " -h") 
        quit()
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    if global_mod.options.xise != None:
        convert_xise(global_mod.options.xise)
        quit()
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    
    # check if manifest is given in the command line
    # if yes, then use it
    # if no, the look for it in the current directory (python manifest has priority)  
    if global_mod.options.manifest != None:
        global_mod.top_manifest = options.manifest
    elif os.path.exists("./manifest.py"):
        global_mod.top_manifest = "./manifest.py"
    elif os.path.exists("./manifest.ini"):
        global_mod.top_manifest = "./manifest.ini"
    else:
        p.echo("No manifest found. At least an empty one is needed")
        quit()
        
    p.vprint("Manifests' scan queue:"+str([global_mod.top_manifest]))
    p.vprint("Parsing manifest: " +str(global_mod.top_manifest))
    
    if global_mod.options.synth_server != None:
        global_mod.synth_server = global_mod.options.synth_server
    if global_mod.options.synth_user != None:
        global_mod.synth_user = global_mod.options.synth_user
    
    global_mod.opt_map = parse_manifest(global_mod.top_manifest) #this call sets global object global_mod.opt_map    
    if global_mod.options.tcl == None:
        if global_mod.opt_map.tcl == None: #option taken, but no tcl given -> find it
            tcl_pat = re.compile("^.*\.tcl$")
            for file in os.listdir("."): #try to find it in the current dir
                if re.match(tcl_pat, file):
                    p.vprint("Found .tcf l file in the current directory: " + file)
                    global_mod.opt_map.tcl = file
                    break
    else:
        global_mod.opt_map.tcl = options.tcl
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    if global_mod.options.fetch == True:
            
        cur_manifest = global_mod.top_manifest 
        involved_modules = []
        new_manifests = []
        
        while True:
            for i in global_mod.opt_map.local:
                if not os.path.exists(i):
                    p.echo("Error in parsing " + cur_manifest +". There is not such catalogue as "+
                    global_mod.cwd + '/' + i)
                    
            p.vprint("Modules waiting in fetch queue:"+
                str(global_mod.opt_map.git) + " " + str(global_mod.opt_map.svn) + " " + str(global_mod.opt_map.local)) 
            
            for i in global_mod.opt_map.svn:
                p.vprint("Checking SVN url: " + i)
                try:
                    url, revision = parse_repo_url(i) 
                    fetch_from_svn(url, revision)
                except ValueError:
                    url = parse_repo_url(i)
                    fetch_from_svn(url)
                except RuntimeError:
                    continue
                
                ret = check_module_and_append(involved_modules, os.path.abspath(global_mod.hdlm_path + "/" + path.url_basename(url)))
                if ret == 0:
                    manifest = search_for_manifest(global_mod.hdlm_path + "/" + path.url_basename(url))
                    if manifest != None:
                        new_manifests.append(manifest)
            global_mod.opt_map.svn = None
            
            for i in global_mod.opt_map.git:
                p.vprint("Checking git url: " + i)
                try:
                    url, revision = parse_repo_url(i)
                    fetch_from_git(url, revision)
                except ValueError:
                    url = parse_repo_url(i)
                    fetch_from_git(url)
                except RuntimeError:
                    continue
                
                if url.endswith(".git"):
                    url = url[:-4]
                
                ret = check_module_and_append(involved_modules, os.path.abspath(global_mod.hdlm_path + "/" + path.url_basename(url)))
                if ret == 0:
                    manifest = search_for_manifest(global_mod.hdlm_path + "/" + path.url_basename(url))
                    if manifest != None:
                        new_manifests.append(manifest)
            global_mod.opt_map.git = None
                    
            for i in global_mod.opt_map.local:
                manifest = search_for_manifest(i)
                if manifest != None:
                    new_manifests.append(manifest)
            involved_modules.extend(global_mod.opt_map.local)
                
            if len(new_manifests) == 0:
                p.vprint("All found manifests have been scanned")
                break
            p.vprint("Manifests' scan queue: " + str(new_manifests))
                
            cur_manifest = new_manifests.pop()
            p.vprint("Parsing manifest: " +str(cur_manifest))
            global_mod.opt_map = parse_manifest(cur_manifest) #this call sets global object global_mod.opt_map
            p.vprint("Involved modules: " + str(involved_modules))        
    
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
        print results.readlines()
        quit()
            
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #            
    if global_mod.options.remote == True:
        if global_mod.opt_map.tcl == None: #option taken, but no tcl given -> find it
            complain_tcl()
            quit()
        if not os.path.exists(global_mod.opt_map.tcl):
            p.echo("Given .tcl doesn't exist: " + global_mod.opt_map.tcl)
            quit()
        
        if not os.path.exists(global_mod.hdlm_path):
            p.echo("There are no modules fetched. Are you sure it's correct?")
        
        p.vprint("The program will be using ssh connection: "+global_mod.synth_user+"@"+global_mod.synth_server)
        global_mod.ssh = Connection(global_mod.synth_user, global_mod.synth_server)
        
        apf = os.path.abspath
        folders_to_be_scanned = [apf(x) for x in global_mod.opt_map.rtl] + [apf(global_mod.hdlm_path)]
        folders_to_be_scanned = list(set(folders_to_be_scanned))
        
        #local_files = make_list_of_files(folders_to_be_scanned)
        if global_mod.opt_map.name != None:
            #dest_folder = transfer_files_forth(local_files, global_mod.opt_map.name)
            dest_folder = global_mod.ssh.transfer_files_forth(folders_to_be_scanned, global_mod.opt_map.name)
        else:
            #dest_folder = transfer_files_forth(local_files)
            dest_folder = global_mod.ssh.transfer_files_forth(folders_to_be_scanned)
        
        ret = global_mod.ssh.system("[ -e /opt/Xilinx/"+global_mod.opt_map.ise+" ]")
        if ret == 1:
            p.echo("There is no "+global_mod.opt_map.ise+" ISE version installed on the remote machine")
            quit()
        
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
        transfer_files_back(dest_folder+global_mod.cwd)
        os.chdir(cur_dir)
        if global_mod.options.no_del != True:
            p.echo("Deleting synthesis folder")
            global_mod.ssh.system('rm -rf ' + dest_folder)
        
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    if global_mod.options.make == True:
        import depend
        
        cur_manifest = global_mod.top_manifest 
        involved_modules = []
        new_manifests = []
        opt_map = global_mod.opt_map
        while True:
            if opt_map.local != None:
                involved_modules.extend(opt_map.local)
                for i in opt_map.local:
                    manifest = search_for_manifest(i)
                    if manifest != None:
                        new_manifests.append(manifest)
                    
            if len(new_manifests) == 0:
                break;
            cur_manifest = new_manifests.pop()
            opt_map = parse_manifest(cur_manifest)
            
        modules = involved_modules
        if os.path.exists(global_mod.hdlm_path):
            modules += [global_mod.hdlm_path+"/"+x for x in os.listdir(global_mod.hdlm_path)]
        if len(modules) == 0:
            p.vprint("No modules were found in " + global_mod.hdlm_path)
        
        #modules += global_mod.opt_map.rtl
        p.vprint("Modules that will be taken into account in the makefile: " + str(modules))
        deps, libs = depend.generate_deps_for_modules(modules)
        depend.generate_makefile(deps, libs)
        
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    if global_mod.options.clean == True:
        if os.path.exists("makefile"):
            p.vprint("Running makefile clean-up")
            os.system("make clean > /dev/null")
        p.vprint("Removing the fetched modules")
        os.system("rm -rf " + global_mod.hdlm_path)
        p.vprint("Removing the makefile")
        os.system("rm -f makefile")
        
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if __name__ == "__main__":
    #global options' map for use in the entire script
    t0 = None
    global_mod.synth_user = "htsynth"
    global_mod.synth_server = "htsynth"
    global_mod.cwd = os.getcwd()
    #globa_mod.ssh = myssh.MySSH(global_mod.synth_user, global_mod.synth_server)
    main()
