#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import msg as p
import global_mod
import path

def fetch_from_svn(url, revision = None, fetchto = None):
    if fetchto == None:
        fetchto = global_mod.fetchto

    if not os.path.exists(fetchto):
        os.mkdir(fetchto)

    cur_dir = os.getcwd()
    os.chdir(fetchto)
    p.echo(os.getcwd())
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

    if not os.path.exists(fetchto):
        os.mkdir(fetchto)

    cur_dir = os.getcwd()
    os.chdir(fetchto)

    basename = url_basename(url)
    if basename.endswith(".git"):
        basename = basename[:-4] #remove trailing .git

    cmd = "git clone " + url
    p.vprint(cmd)
    os.system(cmd)
    if revision:
        os.chdir(basename)
        os.system("git checkout " + revision)
    os.chdir(cur_dir)


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
