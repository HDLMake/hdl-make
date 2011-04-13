#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import msg as p
import mnfst

def url_basename(url):
    """
    Get basename from an url
    """
    if url[-1] == '/':
        ret = os.path.basename(url[:-1])
    else:
        ret = os.path.basename(url)
    return ret

def pathsplit(p, rest=[]):
    (h,t) = os.path.split(p)
    if len(h) < 1: return [t]+rest
    if len(t) < 1: return [h]+rest
    return pathsplit(h,[t]+rest)

def commonpath(l1, l2, common=[]):
    if len(l1) < 1: return (common, l1, l2)
    if len(l2) < 1: return (common, l1, l2)
    if l1[0] != l2[0]: return (common, l1, l2)
    return commonpath(l1[1:], l2[1:], common+[l1[0]])

def is_rel_path(path):
    path = str(path)
    s = path[0]
    if s == '/' or s == '~':
        return False
    return True

def is_abs_path(path):
    path = str(path)
    s = path[0]
    if s == '/':
        return True
    return False
    
def relpath(p1, p2 = None):
    if p2 == None:
        p2 = os.getcwd()
    p1, p2 = p2, p1
    if p1[-1] == '/':
        p1 = p1[:-1]
    if p2[-1] == '/':
        p2 = p2[:-1]

    (common,l1,l2) = commonpath(pathsplit(p1), pathsplit(p2))
    p = []
    if len(l1) > 0:
        p = [ '../' * len(l1) ]
    p = p + l2
    return os.path.join( *p )

#def filter_files(files, extension):
#   

def rel2abs(path, base = os.curdir):
    """
    converts a relative path to an absolute path.

    @param path the path to convert - if already absolute, is returned
    without conversion.
    @param base - optional. Defaults to the current directory.
    The base is intelligently concatenated to the given relative path.
    @return the relative path of path from base
    """
    if os.path.isabs(path): return path
    retval = os.path.join(base,path)
    return os.path.abspath(retval)

def search_for_manifest(search_path):
    """
    Look for manifest in the given folder
    """
    p.vprint("Looking for manifest in " + search_path)
    for filename in os.listdir(search_path):
        if filename == "manifest.py" and not os.path.isdir(filename):
            return os.path.abspath(os.path.join(search_path, filename))
    # no manifest file found
    return None

def make_list_of_files(module_manifest_dict, file_type = None):
    """
    Make list of all files included in the list of folders

    take_files - files specified directly in manifest. If there are some, we should take only them
    file_type - file extension for filtering - if given, only this extension will be taken into account
    """
    p.vpprint(module_manifest_dict)
    def get_files(path, file_type = None):
        """
        Get lists of normal files and list folders recursively
        """
        ret = []
        for filename in os.listdir(path):
            if filename[0] == ".": #a hidden file/catalogue -> skip
                continue
            if os.path.isdir(os.path.join(path, filename)):
                ret.extend(get_files(os.path.join(path, filename), file_type))
            else:
                if file_type == None:
                    ret.append(os.path.abspath(os.path.join(path, filename)))
                else:
                    tmp = filename.rsplit('.')
                    ext = tmp[len(tmp)-1]
                    if ext == file_type:
                        ret.append(os.path.abspath(os.path.join(path, filename)))
        return ret

    files = []
    module_files_dict = {}

    for module in list(module_manifest_dict.keys()): #iterate over all modules
        manifest = module_manifest_dict[module]
        module_files_dict[module] = []
        if manifest != None:
            manifest = mnfst.parse_manifest(manifest) #if found, parse it
            if manifest.files != None and manifest.files != []:
                for file in manifest.files:
                    if os.path.isdir(file):
                        module_files_dict[module].extend(get_files(file, file_type))
                    else:
                        module_files_dict[module].append(file)
            else:
                module_files_dict[module].extend(get_files(module, file_type))
        else:
            module_files_dict[module].extend(get_files(module, file_type))
    return module_files_dict 

def make_list_of_modules(top_manifest, top_opt_map):
    cur_manifest = top_manifest 
    cur_module = os.path.dirname(top_manifest)
    module_manifest_dict = {}
    modules = []
    new_manifests = []
    opt_map = top_opt_map

    module_manifest_dict[os.path.dirname(top_manifest)] = top_manifest
    while True:
        if opt_map.root_manifest != None:
            root_manifest = opt_map.root_manifest
            root_module = os.path.dirname(root_manifest)
            module_manifest_dict[root_module] = root_manifest
            new_manifests.append(root_manifest)
        if opt_map.local != []:
            modules.extend(opt_map.local)
            for i in opt_map.local:
                manifest = search_for_manifest(i)
                if manifest != None:
                    module_manifest_dict[i] = manifest
                    new_manifests.append(manifest)
                else:
                    module_manifest_dict[i] = None

        if opt_map.git != []:
            for i in opt_map.git:
                module_git = os.path.join(opt_map.fetchto, url_basename(i))
                modules.append(module_git)
                manifest = search_for_manifest(module_git)
                if manifest != None:
                    module_manifest_dict[module_git] = manifest
                    new_manifests.append(manifest)
                else:
                    module_manifest_dict[module_git] = None

        if opt_map.svn != []:
            for i in opt_map.svn:
                module_svn = os.path.join(opt_map.fetchto, url_basename(i))
                modules.append(module_svn)
                manifest = search_for_manifest(module_svn)
                if manifest != None:
                    module_manfiest_dict[module_svn] = manifest
                    new_manifests.append(manifest)
                else:
                    module_manifest_dict[module_svn] = None

        if len(new_manifests) == 0:
            break;
        cur_manifest = new_manifests.pop()
        cur_module = os.path.dirname(cur_manifest)
        opt_map = mnfst.parse_manifest(cur_manifest)

    #if os.path.exists(top_opt_map.fetchto):
    #    modules += [os.path.join(top_opt_map.fetchto, x) for x in os.listdir(top_opt_map.fetchto) if os.path.isdir(x)]
    if len(modules) == 0:
        p.vprint("No modules were found in " + top_opt_map.fetchto)
    return module_manifest_dict