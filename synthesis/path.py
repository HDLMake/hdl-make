#!/usr/bin/python
# -*- coding: utf-8 -*-
import os

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
def is_abs_path(path):
    path = str(path)
    s = path[0]
    if s == '~' or s == '/':
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
    
def make_list_of_files(modules, take_files = None, base_folder = None):
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
        
    files = []
    if not isinstance(modules, list):
        files =  getfiles(modules)
    else:
        for module in modules:
            files.extend(getfiles(module))
            
    if take_files != None and take_files != []:
        ret_files = []
        for file in files:
            for take_file in take_files:
                if base_folder+'/'+take_file in os.path.abspath(file):
                    ret_files.append(file)
        return ret_files
    else:
        return files
