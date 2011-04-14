# -*- coding: utf-8 -*-
import os
import sys
import path
import msg as p
import fetch
from fetch import fetch_from_svn, fetch_from_git

if sys.version_info < (3,0):
    import cfgparse2 as cfg
else:
    import cfgparse3 as cfg



def check_correctness(manifest_file):
    m = parse_manifest(manifest_file)
    if m.fetchto != None:
        if is_abs_path(m.fetchto):
            p.echo("fetchto parameter should be a relative path")
        if not os.path.exists(m.fetchto):
            p.echo("fetchto parameter should exist")
    if m.root_manifest != None:
        if not os.path.exists(m.root_manifest):
            p.echo("root_manifest should exist")
        if not os.path.basename(m.root_manfiest) == "manifest.py":
            p.echo("root_manifest should be called \"manfiest.py\"")
    if not isinstance(m.name, basestring):
        p.echo("name parameter should be a string")
    if m.tcl != None:
        if is_abs_path(m.fetchto):
            p.echo("tcl parameter should be a relative path")
        if not os.path.exists(m.fetchto):
            p.echo("tcl parameter should indicate exisiting tcl file")
    if m.ise != None:
        try:
            tcl = float(m.tcl)
        except ValueError:
            p.echo("tcl parameter must have %4.1f format")

    if m.vsim_opt != "":
        if not isinstance(m.vsim_opt, basestring):
            p.echo("vsim_opt must be a string")
    if m.vcom_opt != "":
        if not isinstance(m.vcom_opt, basestring):
            p.echo("vcom_opt must be a string")
    if m.vlog_opt != "":
        if not isinstance(m.vlog_opt, basestring):
            p.echo("vlog_opt must be a string")
    if m.vmap_opt != "":
        if not isinstance(m.vmap_opt, basestring):
            p.echo("vmap_opt must be a string")

    if m.svn != None:
        if not isinstance(m.svn, [basestring,list]):
            p.echo("modules.svn has strange format (neither string nor list)")
    if m.git != None:
        if not isinstance(m.git, [basestring,list]):
            p.echo("modules.svn has strange format (neither string nor list)")
    if m.local != None:
        if not isinstance(m.local, [basestring,list]):
            p.echo("modules.svn has strange format (neither string nor list)")

def init_manifest_parser():
    manifest_parser = cfg.ConfigParser(description="Configuration options description", allow_py = True)
    manifest_parser.add_option('fetchto', default=None, help="Destination for fetched modules") 
    manifest_parser.add_option('root_manifest', default=None, help="Path to root manifest for currently parsed")
    manifest_parser.add_option('name', default=None, help="Name of the folder at remote synthesis machine")
    manifest_parser.add_option('tcl', default=None, help="Path to .tcl file used in synthesis")
    manifest_parser.add_option('ise', default=None, help="Version of ISE to be used in synthesis")
    manifest_parser.add_option('vsim_opt', default="", help="Additional options for vsim")
    manifest_parser.add_option('vcom_opt', default="", help="Additional options for vcom")
    manifest_parser.add_option('vlog_opt', default="", help="Additional options for vlog")
    manifest_parser.add_option('vmap_opt', default="", help="Additional options for vmap")
    manifest_parser.add_option('modules', dest="svn", keys="svn", default=None,
    help="List of modules to be fetched from SVN")
    manifest_parser.add_option('modules', dest="git", keys="git", default=None,
    help="List of modules to be fetched from git")
    manifest_parser.add_option('modules', dest="local", keys="local", default=None,
    help="List of local modules")
    manifest_parser.add_option('library', dest="library", default="work",
    help="Destination library for module's VHDL files")
    manifest_parser.add_option('files', default=None, help="List of files from the current module")
    return manifest_parser

def parse_manifest(manifest_file):
    p.vprint("Parsing manifest file: " + manifest_file)
    manifest_path = os.path.dirname(manifest_file)

    manifest_parser = init_manifest_parser()
    manifest_parser.add_file(manifest_file)

    opt_map = None
    try:
        opt_map = manifest_parser.parse()
    except NameError as ne:
        p.echo("Error while parsing {0}:\n{1}: {2}.".format(manifest_file, type(ne), ne))
        quit()

    if opt_map.root_manifest != None:
        opt_map.root_manifest = path.rel2abs(opt_map.root_manifest, os.path.dirname(manifest_file))
        if not os.path.exists(opt_map.root_manifest):
            p.echo("Error while parsing " + manifest_file + ". Root manifest doesn't exist: "
            + opt_map.root_manifest)
            quit()
    if opt_map.fetchto == None:
        opt_map.fetchto = os.path.dirname(manifest_file)
    else:
        if not path.is_rel_path(opt_map.fetchto):
            p.echo(' '.join([os.path.basename(sys.argv[0]), "accepts relative paths only:", opt_map.fetchto]))
            quit()
        opt_map.fetchto = path.rel2abs(opt_map.fetchto, manifest_path)

    if opt_map.ise == None:
        opt_map.ise = "13.1"

    opt_map.local = make_list(opt_map.local)
    for i in opt_map.local:
        if not path.is_rel_path(i):
            p.echo(os.path.basename(sys.argv[0]) + " accepts relative paths only: " + i)
            quit()
    opt_map.local = [path.rel2abs(x, manifest_path) for x in opt_map.local]

    opt_map.files = make_list(opt_map.files)
    files = []
    for file in opt_map.files:
        if not path.is_abs_path(file):
            files.append(path.rel2abs(file, manifest_path))
    opt_map.files = files

    opt_map.svn = make_list(opt_map.svn)
    opt_map.git = make_list(opt_map.git)
    opt_map.files = make_list(opt_map.files)
    return opt_map

def check_module_and_append(list, module):
    """
    Appends a module to the list if it doesn't belong to it. If it is already there, complain
    """
    if list.count(module) != 0:
        p.echo("Module " + module + " has been previously defined: ommiting")
        return 1 
    for i in list:
        if os.path.basename(i) == os.path.basename(module):
            p.echo("Module " + module + " has the same name as " + i + " :ommiting")
            return 1
    list.append(module)
    return 0

def fetch_manifest(manifest_path, opt_map):
    cur_manifest = manifest_path
    cur_opt_map = opt_map
    top_module_dir = os.path.dirname(manifest_path)
    involved_modules = [top_module_dir]
    new_manifests = [manifest_path]

    p.vprint("Fetching manifest: " + manifest_path)

    while len(new_manifests) > 0:
        if cur_opt_map.root_manifest != None:
            root_manifest = cur_opt_map.root_manifest
            p.vprint("Encountered root manifest: " + root_manifest)
            root_manifest_modules = fetch_manifest(root_manifest, parse_manifest(root_manifest))
            involved_modules.extend(root_manifest_modules)
        for i in cur_opt_map.local:
            if not os.path.exists(path.rel2abs(i, os.path.dirname(cur_manifest))):
                p.echo("Error in parsing " + cur_manifest +". There is not such catalogue as "+
                path.rel2abs(i, os.path.dirname(cur_manifest)))

        p.vprint("Modules waiting in fetch queue:"+
            ' '.join([str(cur_opt_map.git), str(cur_opt_map.svn), str(cur_opt_map.local)]))

        for i in cur_opt_map.svn:
            p.vprint("Checking SVN url: " + i)
            fetch_from_svn(fetch.parse_repo_url(i), fetchto = cur_opt_map.fetchto)
            p.vprint("Fetching to " + cur_opt_map.fetchto)
            ret = check_module_and_append(involved_modules, i)
            if ret == 0:
                manifest = path.search_for_manifest(os.path.join(cur_opt_map.fetchto, path.url_basename(i)))
                if manifest != None:
                    new_manifests.append(manifest)

        for i in cur_opt_map.git:
            p.vprint("Checking git url: " + i)
            fetch_from_git(fetch.parse_repo_url(i), fetchto = cur_opt_map.fetchto)

            if url.endswith(".git"):
                url = url[:-4]

            ret = check_module_and_append(involved_modules, i)
            if ret == 0:
                manifest = path.search_for_manifest(os.path.join(global_mod.fetchto, path.url_basename(url)))
                if manifest != None:
                    new_manifests.append(manifest)

        for i in cur_opt_map.local:
            manifest = path.search_for_manifest(i)
            if manifest != None:
                new_manifests.append(manifest)
        involved_modules.extend(cur_opt_map.local)

        p.vprint("Manifests' scan queue: " + str(new_manifests))

        cur_manifest = new_manifests.pop()
        cur_opt_map = parse_manifest(cur_manifest) #this call sets global object global_mod.opt_map
    #p.vprint("Involved modules: " + str(involved_modules
    
    p.vprint("All found manifests have been scanned")
    return involved_modules
