#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import msg as p
import global_mod
import path


class ModuleFetcher:

    def __init__(self, fetch_dir = None):
        pass

# inputs:
# - type of the module (local/git/svn)
    def fetch(self, mod_type, mod_url):
        pass

    def 

class ModulePool:




def fetch_from_svn(url, revision = None, fetchto = None):
    if fetchto == None:
        fetchto = global_mod.fetchto

    if not os.path.exists(fetchto):
        os.mkdir(fetchto)

    cur_dir = os.getcwd()
    os.chdir(fetchto)
    basename = path.url_basename(url)

    cmd = "svn checkout {0} " + basename
    if revision:
        cmd = cmd.format(url + '@' + revision)
    else:
        cmd = cmd.format(url)

    p.vprint(cmd)
    os.system(cmd)
    os.chdir(cur_dir)

def fetch_from_git(url, revision = None, fetchto = None):
    if fetchto == None:
        fetchto = global_mod.fetchto

    basename = path.url_basename(url)
    if basename.endswith(".git"):
        basename = basename[:-4] #remove trailing .git

    if not os.path.exists(fetchto):
        os.mkdir(fetchto)

    if not os.path.exists(fetchto+"/"+basename):
        update_only = False
    else:
        update_only = True

    cur_dir = os.getcwd()
    os.chdir(fetchto)


    if update_only:
        cmd = "git --git-dir="+basename+"/.git pull"
    else:  		
        cmd = "git clone " + url
	    
    rval = True
    if os.system(cmd) != 0:
        rval = False

    if revision and rval:
        os.chdir(basename)
        if os.system("git checkout " + revision) != 0:
            rval = False
            
    os.chdir(cur_dir)
    return rval


def parse_repo_url(url) :
    """
    Check if link to a repo seems to be correct
    """
    import re
    url_pat = re.compile("[ \t]*([^ \t]+)[ \t]*(@[ \t]*(.+))?[ \t]*")
    url_match = re.match(url_pat, url)

    if url_match == None:
        p.echo("Not a correct repo url: {0}. Skipping".format(url))
    if url_match.group(3) != None: #there is a revision given 
        ret = (url_match.group(1), url_match.group(3))
    else:
        ret = url_match.group(1)
    return ret


