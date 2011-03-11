#!/usr/bin/python
# -*- coding: utf-8 -*-

import cfgparse
import re
import fileinput
import sys
import relpath
import time
import os
import myssh
import random
import string
import global_mod
from msg import my_msg
from msg import v_msg
from optparse import OptionParser

def complain_tcl():
    print "For Xilinx synthesis a tcl file in the top module is required"

def make_list_of_files(modules):
    """
    Make list of all files included in the list of folders
    """
    def getfiles(path):
        """
        Get lists of normal files and list folders recursively
        """
        ret = []
        for filename in os.listdir(path):
            if filename[0] == ".": #a hidden file/catalogue -> skip
                continue
            if os.path.isdir(path + "/" + filename):
                ret.extend(getfiles(path + "/" + filename))
            else:
                ret.append(path + "/" + filename)
        return ret
        
    if not isinstance(modules, list):
        return getfiles(modules)
    files = []
    for module in modules:
        files.extend(getfiles(module))
    return files

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
    
def url_basename(url):
    """
    Get basename from an url
    """
    if url[-1] == '/':
        ret = os.path.basename(url[:-1])
    else:
        ret = os.path.basename(url)
    return ret
   
def fetch_from_svn(url, revision = None):
    basename = url_basename(url)
    
    global hdlm_path
    cmd = "svn checkout {0} " + hdlm_path + "/" + basename
    if revision:
        cmd = cmd.format(url + '@' + revision)
    else:
        cmd = cmd.format(url)
        
    v_msg(cmd)
    os.system(cmd)

def fetch_from_local(url):
    if not os.path.exists(url):
        my_msg("Local URL " + url + " not found\nQuitting")
        quit()
    basename = url_basename(url)
    global hdlm_path
    if os.path.exists(hdlm_path + "/" + basename):
        my_msg("Folder " + hdlm_path + "/" + basename + " exists. Maybe it is already fetched?")
        return
    os.symlink(url, hdlm_path + "/" + basename)

def fetch_from_git(url, revision = None):
    cwd = os.getcwd()
    basename = url_basename(url)
    
    if basename.endswith(".git"):
        basename = basename[:-4] #remove trailing .git
    global hdlm_path
    os.chdir(hdlm_path)
    cmd = "git clone " + url
    v_msg(cmd)
    os.system(cmd)
    if revision:
        os.chdir(basename)
        os.system("git checkout " + revision)
        
    os.chdir(cwd)

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
    global_mod.opt_map = manifest_parser.parse()
    
    if global_mod.opt_map.root == None:
        global_mod.opt_map.root = "."
        
    if global_mod.opt_map.rtl == None:
        global_mod.opt_map.rtl = ["."]
    elif not isinstance (global_mod.opt_map.rtl, list):
        global_mod.opt_map.rtl = [global_mod.opt_map.rtl]

    if global_mod.opt_map.ise == None:
        global_mod.opt_map.ise = "13.1"
        
    if global_mod.opt_map.local != None: 
        if not isinstance(global_mod.opt_map.local, (list, tuple)):
            global_mod.opt_map.local = [global_mod.opt_map.local]
        for i in global_mod.opt_map.local:
            if relpath.is_abs_path(i):
                my_msg(sys.argv[0] + " accepts relative paths only: " + i)
                quit()
        #global_mod.opt_map.local[:] = [x for x in global_mod.opt_map.local if not relpath.is_abs_path(

    if global_mod.opt_map.svn != None and not isinstance(global_mod.opt_map.svn, (list, tuple)):
        global_mod.opt_map.svn = [global_mod.opt_map.svn]
    if global_mod.opt_map.git != None and not isinstance(global_mod.opt_map.git, (list, tuple)):
        global_mod.opt_map.git = [global_mod.opt_map.git]
    if global_mod.opt_map.files != None and not isinstance(global_mod.opt_map.files, (list, tuple)):
        global_mod.opt_map.files = [global_mod.opt_map.files]
    return global_mod.opt_map
 
def transfer_files_forth(files, dest_folder = None):
    """
    Takes list of files and sends them to remote machine. Name of a directory, where files are put
    is returned
    """
    if not isinstance(files, list):
        return None;
    
    ssh_cmd = "ssh " + global_mod.synth_user + "@" + global_mod.synth_server
    
    ''.join(random.choice(string.ascii_letters + string.digits) for x in range(8))
    #create a randstring for a new catalogue on remote machine
    
    #create a new catalogue on remote machine
    if dest_folder == None:
        dest_folder = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(8)) 
        
    mkdir_cmd = 'mkdir ' + dest_folder 
    v_msg("Connecting to " + ssh_cmd + " and creating directory " + dest_folder + ": " + mkdir_cmd)
    global_mod.ssh.system(mkdir_cmd)
    
    #create a string with filenames
    from pipes import quote
    local_files_str = ' '.join(quote(os.path.abspath(x)) for x in files)
    
    rsync_cmd = "rsync -Rav " + local_files_str + " " + global_mod.synth_user + "@" + global_mod.synth_server + ":" + dest_folder 
    #v_msg("Coping " + str(len(local_files_str)) + " files to remote server: " + rsync_cmd)
    #os.system(rsync_cmd)
    import subprocess
    p = subprocess.Popen(rsync_cmd, shell=True)
    os.waitpid(p.pid, 0)[1]
    print "done"
    return dest_folder 
    
def transfer_files_back(dest_folder):
    rsync_cmd = "rsync -av " + global_mod.synth_user + "@" + global_mod.synth_server + ":" + dest_folder+" ."
    v_msg(rsync_cmd)
    os.system(rsync_cmd)
    
def convert_xise(xise):
    if not os.path.exists(xise):
        my_msg("Given .xise file does not exist:" + xise)
        quit()
        
    global hdlm_path
    modules = ["."]
    modules.append(hdlm_path)
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
            file_basename = url_basename(m.group(2))
            found = False
            for file in files:
                if file_basename in file:
                    found = True
                    new_ise.append(m.group(1) + relpath.relpath(os.path.abspath("."), file) + m.group(3))
                    break
            if found == False:
                my_msg("Not found proper file for " + filename)
                new_ise.append(line)
        else:
            new_ise.append(line + "\n")
    
    new_ise_file = open(xise + ".new", "w")
    
def search_for_manifest(search_path):
    """
    Look for manifest in the given folder ans subfolders
    """
    cmd = "find -H " + search_path + " -name manifest.py"
    v_msg(cmd)
    files = os.popen(cmd).readlines()
    
    if len(files) == 0:
        v_msg("No manifest found in: " + search_path)
        return None
    elif len(files) > 1:
        my_msg("Too many manifests in" + search_path)
        return files[0] 
        
    print("Found manifest: " + os.path.abspath(files[0]).strip())
    return os.path.abspath(files[0]).strip()     
                
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
    
    global hdlm_path

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    #Check if any option was selected
    if global_mod.options.local == global_mod.options.fetch == global_mod.options.remote == global_mod.options.make == global_mod.options.clean == None:
        import sys
        my_msg("Are you sure you didn't forget to specify an option? At least one?")
        my_msg("Maybe you should try " + sys.argv[0] + " -h") 
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
        my_msg("No manifest found. At least an empty one is needed")
        quit()
        
    v_msg("Manifests' scan queue:"+str([global_mod.top_manifest]))
    v_msg("Parsing manifest: " +str(global_mod.top_manifest))
    
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
                    v_msg("Found .tcl file in the current directory: " + file)
                    global_mod.opt_map.tcl = file
                    break
    else:
        global_mod.opt_map.tcl = options.tcl
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    if global_mod.options.fetch == True:
        if not os.path.exists(hdlm_path):
            os.mkdir(hdlm_path)
            
        cur_manifest = top_manifest 
        involved_modules = []
        new_manifests = []
        
        while True:
            for i in global_mod.opt_map.local:
                if not os.path.exists(manifest_path + '/' + i):
                    my_msg("Error in parsing " + manifest_file +". There is not such catalogue as "+
                    manifest_path + '/' + i)
                    
            v_msg("Modules waiting in fetch queue:"+
                str(global_mod.opt_map.git) + " " + str(global_mod.opt_map.svn) + " " + str(global_mod.opt_map.local)) 
            
            if global_mod.opt_map.svn != None:
                for i in global_mod.opt_map.svn:
                    v_msg("Checking SVN url: " + i)
                    try:
                        url, revision = parse_repo_url(i) 
                        fetch_from_svn(url, revision)
                    except ValueError:
                        url = parse_repo_url(i)
                        fetch_from_svn(url)
                    except RuntimeError:
                        continue
                    
                    ret = check_module_and_append(involved_modules, os.path.abspath(hdlm_path + "/" + url_basename(url)))
                    if ret == 0:
                        manifest = search_for_manifest(hdlm_path + "/" + url_basename(url))
                        if manifest != None:
                            new_manifests.append(manifest)
                global_mod.opt_map.svn = None
            
            if global_mod.opt_map.git != None: 
                for i in global_mod.opt_map.git:
                    v_msg("Checking git url: " + i)
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
                    
                    ret = check_module_and_append(involved_modules, os.path.abspath(hdlm_path + "/" + url_basename(url)))
                    if ret == 0:
                        manifest = search_for_manifest(hdlm_path + "/" + url_basename(url))
                        if manifest != None:
                            new_manifests.append(manifest)
                global_mod.opt_map.git = None
                    
            if global_mod.opt_map.local != None:
                for i in global_mod.opt_map.local:
                    i = os.path.abspath(relpath.rel2abs(os.path.expanduser(i), os.path.dirname(cur_manifest)))
                    v_msg("Checking local url: " + i)
                    try:
                        url, revision = i
                        print "Revision number not allowed in local URLs"
                        continue
                    except ValueError:
                        url = i
                        if not os.path.exists(url):
                            print "Specified module (" + url + ") does not exist"
                            print "Ommitting"
                            continue
                        fetch_from_local(url)
                    ret = check_module_and_append(involved_modules, os.path.abspath(hdlm_path + "/" + url_basename(url)))
                    if ret == 0:
                        manifest = search_for_manifest(url)
                        if manifest != None:
                            new_manifests.append(manifest)
                global_mod.opt_map.local = None
            if len(new_manifests) == 0:
                v_msg("All found manifests have been scanned")
                break
            v_msg("Manifests' scan queue: " + str(new_manifests))
                
            cur_manifest = new_manifests.pop()
            v_msg("Parsing manifest: " +str(cur_manifest))
            global_mod.opt_map = parse_manifest(cur_manifest) #this call sets global object global_mod.opt_map
            v_msg("Involved modules: " + str(involved_modules))        
    
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    if global_mod.options.local == True:
        if global_mod.opt_map.tcl == None:
            complain_tcl()
            quit()
        if not os.path.exists("/opt/Xilinx/" + global_mod.opt_map.ise):
            my_msg("The script can't find demanded ISE version: " + global_mod.opt_map.ise)
            quit()
        
        address_length = check_address_length(os)
        if address_length == 32 or address_length == None:
            path_ext = global_mod.ise_path_32[global_mod.opt_map.ise]  
        else:
            my_msg("Don't know how to run settings script for ISE version: " + global_mod.opt_map.ise)
        results = os.popen("export PATH=$PATH:"+path_ext+" &&xtclsh " + global_mod.opt_map.tcl + " run_process")
        print results.readlines()
        quit()
            
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #            
    if global_mod.options.remote == True:
        if global_mod.opt_map.tcl == None: #option taken, but no tcl given -> find it
            complain_tcl()
            quit()
        if not os.path.exists(global_mod.opt_map.tcl):
            my_msg("Given .tcl doesn't exist: " + global_mod.opt_map.tcl)
            quit()
        
        if not os.path.exists(hdlm_path):
            my_msg("There are no modules fetched. Are you sure it's correct?")
        
        v_msg("The program will be using ssh connection: "+global_mod.synth_user+"@"+global_mod.synth_server)
        global_mod.ssh = myssh.MySSH(global_mod.synth_user, global_mod.synth_server)
        
        apf = os.path.abspath
        folders_to_be_scanned = [apf(x) for x in global_mod.opt_map.rtl] + [apf(hdlm_path)]
        folders_to_be_scanned = list(set(folders_to_be_scanned))
        
        #local_files = make_list_of_files(folders_to_be_scanned)
        if global_mod.opt_map.name != None:
            #dest_folder = transfer_files_forth(local_files, global_mod.opt_map.name)
            dest_folder = transfer_files_forth(folders_to_be_scanned, global_mod.opt_map.name)
        else:
            #dest_folder = transfer_files_forth(local_files)
            dest_folder = transfer_files_forth(folders_to_be_scanned)
        
        ssh_cmd = "ssh " + global_mod.synth_user + "@" + global_mod.synth_server
        
        ret = global_mod.ssh.system("[ -e /opt/Xilinx/"+global_mod.opt_map.ise+" ]")
        if ret == 1:
            my_msg("There is no "+global_mod.opt_map.ise+" ISE version installed on the remote machine")
            quit()
        
        address_length = check_address_length(global_mod.ssh)
        if address_length == 32 or address_length == None:
            path_ext = global_mod.ise_path_32[global_mod.opt_map.ise]
        else:
            path_ext = global_mod.ise_path_64[global_mod.opt_map.ise]
            
        syn_cmd ="PATH=$PATH:"+path_ext+"&& cd "+dest_folder+global_mod.cwd+"&& xtclsh "+global_mod.opt_map.tcl+" run_process"
        v_msg("Launching synthesis on " + global_mod.synth_server + ": " + syn_cmd)
        global_mod.ssh.system(syn_cmd)
        
        cur_dir = os.path.basename(global_mod.cwd)
        os.chdir("..")
        transfer_files_back(dest_folder+global_mod.cwd)
        os.chdir(cur_dir)
        if global_mod.options.no_del != True:
            global_mod.ssh.system('rm -rf ' + dest_folder)
        
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    if global_mod.options.make == True:
        import depend
        if not os.path.exists(hdlm_path):
            my_msg("There is no "+hdlm_path+" catalog. Probably modules are not fetched?")
            quit()
            
        modules = os.listdir(hdlm_path)
        if len(modules) == 0:
            v_msg("No modules were found in " + hdlm_path)
        modules = [hdlm_path + "/" + x for x in modules] + global_mod.opt_map.rtl
        v_msg("Modules that will be taken into account in the makefile: " + str(modules))
        deps = depend.generate_deps_for_modules(modules)
        depend.generate_makefile(deps)
        
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    if global_mod.options.clean == True:
        if os.path.exists("makefile"):
            v_msg("Running makefile clean-up")
            os.system("make clean > /dev/null")
        v_msg("Removing the fetched modules")
        os.system("rm -rf " + hdlm_path)
        v_msg("Removing the makefile")
        os.system("rm -f makefile")
        
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        
if __name__ == "__main__":
    #global options' map for use in the entire script
    t0 = None
    hdlm_path="hdl_make"
    global_mod.synth_user = "htsynth"
    global_mod.synth_server = "htsynth"
    global_mod.cwd = os.getcwd()
    #globa_mod.ssh = myssh.MySSH(global_mod.synth_user, global_mod.synth_server)
    main()
