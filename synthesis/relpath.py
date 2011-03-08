#!/usr/bin/python
# -*- coding: utf-8 -*-
import os

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
    
def relpath(p1, p2):
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

def test(p1,p2):
    print "from", p1, "to", p2, " -> ", relpath(p1, p2)
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
        
        
if __name__ == '__main__':
    test(os.getcwd(), os.path.expanduser('~/cern/matthieu'))
    test(os.getcwd(), "/home/pawel/cern/matthieu")
