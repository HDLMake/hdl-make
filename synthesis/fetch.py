#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import msg as p
import global_mod
import path

def fetch_from_svn(url, revision = None):
    basename = path.url_basename(url)
    
    cmd = "svn checkout {0} " + global_mod.hdlm_path + "/" + basename
    if revision:
        cmd = cmd.format(url + '@' + revision)
    else:
        cmd = cmd.format(url)
        
    p.vprint(cmd)
    os.system(cmd)

def fetch_from_local(url):
    if not os.path.exists(url):
        p.echo("Local URL " + url + " not found\nQuitting")
        quit()
    basename = path.url_basename(url)
    
    make_hdlm_dir()
    if os.path.exists(global_mod.hdlm_path + "/" + basename):
        p.echo("Folder " + global_mod.hdlm_path + "/" + basename + " exists. Maybe it is already fetched?")
        return
    os.symlink(url, global_mod.hdlm_path + "/" + basename)

def fetch_from_git(url, revision = None):
    make_hdlm_dir()
    
    basename = url_basename(url)
    if basename.endswith(".git"):
        basename = basename[:-4] #remove trailing .git
    os.chdir(global_mod.hdlm_path)
    cmd = "git clone " + url
    p.vprint(cmd)
    os.system(cmd)
    if revision:
        os.chdir(basename)
        os.system("git checkout " + revision)
        
    os.chdir(global_mod.cwd)
    
def make_hdlm_dir():
    if not os.path.exists(global_mod.hdlm_path):
        os.mkdir(global_mod.hdlm_path)