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

def complain_manifest():
    print """There is no manifest file in the driectory
It is therefore assumed that no external files are needed
and the synthesis is made locally"""
    
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
        opt_map.ise = "12.1"
        
    if opt_map.local != None and not isinstance(opt_map.local, (list, tuple)):
        opt_map.local = [opt_map.local]
    for i in opt_map.local:
        if relpath.is_abs_path(i):
            my_msg(sys.argv[0] + " accepts relative paths only: " + i)
            quit()
    #opt_map.local[:] = [x for x in opt_map.local if not relpath.is_abs_path(
    for i in opt_map.local:
        if not os.path.exists(manifest_path + '/' + i):
            my_msg("Error in parsing " + manifest_file +". There is not such catalogue as "+
                manifest_path + '/' + i)
            quit()
    if opt_map.svn != None and not isinstance(opt_map.svn, (list, tuple)):
        opt_map.svn = [opt_map.svn]
    if opt_map.git != None and not isinstance(opt_map.git, (list, tuple)):
        opt_map.git = [opt_map.git]
    if opt_map.files != None and not isinstance(opt_map.files, (list, tuple)):
        opt_map.files = [opt_map.files]
    return opt_map
 
def transfer_files_forth(files):
    """
    Takes list of files and sends them to remote machine. Name of a directory, where files are put
    is returned
    """
    if not isinstance(files, list):
        return None;
    
    global synth_server
    global synth_user
    global ssh
    ssh_cmd = "ssh " + synth_user + "@" + synth_server
    
    randstring = ''.join(random.choice(string.ascii_letters + string.digits) for x in range(8))
    #create a randstring for a new catalogue on remote machine
    v_msg("Generated randstring " + randstring)
    
    #create a new catalogue on remote machine
    mkdir_cmd = 'mkdir ' + randstring
    v_msg("Connecting to " + ssh_cmd + " and creating directory " + randstring + ": " + mkdir_cmd)
    ssh.system(mkdir_cmd)
    
    #create a string with filenames
    lcl_files_str = ''.join(os.path.abspath(x) + ' ' for x in files)
    
    cp_cmd = "tar -cvjf - " + lcl_files_str + "|" + ssh_cmd + ' "(cd ' + randstring + '; tar xjf -)"'
    v_msg("Coping files to remote server: " + cp_cmd)
    os.system(cp_cmd)
    return randstring
    
def transfer_files_back(files, randstring):
    global synth_user
    global synth_server
    global ssh
    v_msg("Creating an archive with new files on the remote machine")
    tar_cmd = 'cd ' + randstring +'&& tar -cjvf '+randstring+'.tar '+str(files)
    ssh.system(tar_cmd)
    scp_cmd = "scp " + synth_user + "@" + synth_server + ":" + randstring+"/"+randstring+".tar ."
    os.system(scp_cmd)
    
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
    (global_mod.options, args) = parser.parse_args()
    
    global hdlm_path        
    # # # # # # # # #
    if global_mod.options.xise != None:
        convert_xise(global_mod.options.xise)
        quit()
    # # # # # # # # #
    
    # check if manifest is given in the command line
    # if yes, then use it
    # if no, the look for it in the current directory (python manifest has priority)  
    global top_manifest
    if global_mod.options.manifest != None:
        top_manifest = options.manifest
    elif os.path.exists("./manifest.py"):
        top_manifest = "./manifest.py"
    elif os.path.exists("./manifest.ini"):
        top_manifest = "./manifest.ini"
    else:
        complain_manifest()
    v_msg("Manifests' scan queue:"+str([top_manifest]))
    v_msg("Parsing manifest: " +str(top_manifest))
    
    global synth_server
    global synth_user
    if global_mod.options.synth_server == None:
        global_mod.options.synth_server = synth_server
    if global_mod.options.synth_user == None:
        global_mod.options.synth_user = synth_user
    
    global opt_map
    opt_map = parse_manifest(top_manifest) #this call sets global object opt_map    
    if global_mod.options.tcl == None:
        if opt_map.tcl == None: #option taken, but no tcl given -> find it
            tcl_pat = re.compile("^.*\.tcl$")
            for file in os.listdir("."): #try to find it in the current dir
                if re.match(tcl_pat, file):
                    v_msg("Found .tcl file in the current directory: " + file)
                    opt_map.tcl = file
                    break
    else:
        opt_map.tcl = options.tcl
    # # # # # # #
    if global_mod.options.fetch == True:
        if not os.path.exists(hdlm_path):
            os.mkdir(hdlm_path)
            
        cur_manifest = top_manifest 
        involved_modules = []
        new_manifests = []
        
        while True:
            v_msg("Modules waiting in fetch queue:"+
                str(opt_map.git) + " " + str(opt_map.svn) + " " + str(opt_map.local)) 
            
            if opt_map.svn != None:
                for i in opt_map.svn:
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
                opt_map.svn = None
            
            if opt_map.git != None: 
                for i in opt_map.git:
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
                opt_map.git = None
                    
            if opt_map.local != None:
                for i in opt_map.local:
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
                opt_map.local = None
            if len(new_manifests) == 0:
                v_msg("All found manifests have been scanned")
                break
            v_msg("Manifests' scan queue: " + str(new_manifests))
                
            cur_manifest = new_manifests.pop()
            v_msg("Parsing manifest: " +str(cur_manifest))
            opt_map = parse_manifest(cur_manifest) #this call sets global object opt_map
            v_msg("Involved modules: " + str(involved_modules))        
    
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    if global_mod.options.local == True:
        if opt_map.tcl == None:
            complain_tcl()
            quit()
        if not os.path.exists("/opt/Xilinx/" + opt_map.ise):
            my_msg("The script can't find demanded ISE version: " + opt_map.ise)
            quit()
        if opt_map.ise == "10.1":
            os.system("source /opt/Xilinx/10.1/ISE/settings32.sh")
        elif opt_map.ise == "12.1":
            os.system("source /opt/Xilinx/12.1/ISE_DS/ISE/settings32.sh")
        else:
            my_msg("Don't know how to run settings script for ISE version: " + opt_map.ise)
        results = os.popen("xtclsh " + opt_map.tcl + " run_process")
        print results.readlines()
        quit()
            
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #            
    if global_mod.options.remote == True:
        if opt_map.tcl == None: #option taken, but no tcl given -> find it
            complain_tc()
            quit()
            
        global ssh
        apf = os.path.abspath
        folders_to_be_scanned = [apf(*opt_map.rtl)] + [apf(hdlm_path)] + [apf(".")]
        folders_to_be_scanned = list(set(folders_to_be_scanned))
        
        local_files = make_list_of_files(folders_to_be_scanned)
        randstring = transfer_files_forth(local_files)
        ssh_cmd = "ssh " + synth_user + "@" + synth_server
        
        #generate command and run remote synthesis
        if float(opt_map.ise) > 12.0:
            syn_cmd = "source /opt/Xilinx/"+opt_map.ise+"/ISE_DS/settings32.sh"
        elif float(opt_map.ise) == 10.1:
            syn_cmd = "source /opt/Xilinx/10.1/ISE/settings32.sh"
        else:
            my_msg("I dont know how to support your ISE version:" + opt_map.ise)
            
        syn_cmd = "source /opt/Xilinx/"+opt_map.ise+"/ISE*/settings32.sh"
        syn_cmd +=" && cd "+randstring +os.path.dirname(os.path.abspath(opt_map.tcl))+" && xtclsh "+opt_map.tcl+" run_process"
        v_msg("Launching synthesis on " + synth_server + ": " + syn_cmd)
        ssh.system(syn_cmd)
        
        ls_cmd = "cd "+randstring+" && find "+" -type f"
        v_msg("Looking for files for back-transfer: " + ls_cmd)
        remote_files = [x.strip() for x in ssh.popen(ls_cmd).readlines()]
        
        #substract local files from remote files
        new_files = list(set([x[1:] for x in remote_files]) - set([os.path.abspath(x) for x in local_files]))
        v_msg("New files created on remote machine: " + str(new_files))
        if len(new_files) == 0:
            my_msg("There are no new files for back-transfer. Probably something went wrong?")
            return
        transfer_files_back(new_files, randstring)
        ssh.system('rm -rf ' + randstring)
        
        import tarfile
        tar = tarfile.open(randstring+".tar")
        tar.extractall(path="/")
        tar.close()
        os.remove(randstring+".tar")
        
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
    if global_mod.options.make == True:
        import depend
        if not os.path.exists(hdlm_path):
            my_msg("There is no .hdl-make catalog. Probably modules are not fetched?")
            quit()
            
        modules = os.listdir(hdlm_path)
        if len(modules) == 0:
            v_msg("No modules were found in " + hdlm_path)
        modules = [hdlm_path + "/" + x for x in modules]
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
    #Check if any option was selected
    if global_mod.options.local == global_mod.options.fetch == global_mod.options.remote == global_mod.options.make == global_mod.options.clean == None:
        my_msg("Are you sure you didn't forget to specify an option? At least one?")
        quit()
        
if __name__ == "__main__":
    #global options' map for use in the entire script
    opt_map = None
    t0 = None
    hdlm_path=".hdl-make"
    top_manifest = ""
    synth_user = "pawel"
    synth_server = "127.0.0.1"
    ssh = myssh.MySSH(synth_user, synth_server)
    main()
