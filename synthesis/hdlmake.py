#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import fileinput
import sys
import path
import path
import time
import os
from connection import Connection
import random
import string
import global_mod
import msg as p
import optparse
from module import Module
from helper_classes import Manifest, ManifestParser
from fetch import ModulePool 


def main():
    global_mod.t0 = time.time()

    parser = optparse.OptionParser()

    parser.add_option("--manifest-help", action="store_true",
    dest="manifest_help", help="print manifest file variables description")

    parser.add_option("-k", "--make", dest="make", action="store_true",
    default=None, help="generate a Makefile (simulation/synthesis)")
    
    parser.add_option("--make-fetch", dest="make_fetch", action="store_true",
    default=None, help="generate a makefile for modules' fetching")

    parser.add_option("-f", "--fetch", action="store_true", dest="fetch",
    help="fetch and/or update remote modules listed in Manifet")

    parser.add_option("--ise-proj", action="store_true", dest="ise_proj",
    help="create/update an ise project including list of project files")

    parser.add_option("-l", "--synthesize-locally", dest="local",
    action="store_true", help="perform a local synthesis")

    parser.add_option("-r", "--synthesize-remotelly", dest="remote",
    action="store_true", help="perform a remote synthesis")

#    parser.add_option("--ipcore", dest="ipcore", action="store_true",
#    default="false", help="generate a pseudo ip-core")

    parser.add_option("--nodel", dest="nodel", action="store_true",
    default="false", help="don't delete intermediate makefiles")

    parser.add_option("--py", dest="arbitrary_code",
    default="", help="add arbitrary code to all manifests' evaluation")

    parser.add_option("--synth-server", dest="synth_server",
    default=None, help="use given SERVER for remote synthesis", metavar="SERVER")

    parser.add_option("--synth-user", dest="synth_user",
    default=None, help="use given USER for remote synthesis", metavar="USER")

    parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
    default="false", help="verbose mode")

    (options, args) = parser.parse_args()
    global_mod.options = options

    if options.manifest_help == True:
        ManifestParser().help()
        quit()

    file = None
    if os.path.exists("manifest.py"):
        file = "manifest.py"
    elif os.path.exists("Manifest.py"):
        file = "Manifest.py"

    if file != None:
        p.vprint("LoadTopManifest");
        top_manifest = Manifest(path=os.path.abspath(file))
        global_mod.top_module = Module(manifest=top_manifest, parent=None, source="local", fetchto=".")

        global_mod.top_module.parse_manifest()
        global_mod.global_target = global_mod.top_module.target
        #global_mod.top_module.fetch()
    else:
        p.echo("No manifest found. At least an empty one is needed")
        quit()

    global_mod.modules_pool = ModulePool(global_mod.top_module)
    global_mod.ssh = Connection(ssh_user=options.synth_user, ssh_server=options.synth_server)

    tm = global_mod.top_module
    pool = global_mod.modules_pool
    ssh = global_mod.ssh
    from action_runner import ActionRunner
    action_runner = ActionRunner(modules_pool=pool, connection=ssh)

    if options.fetch == True:
        action_runner.fetch()
    elif options.local == True:
        action_runner.run_local_synthesis()
    elif options.remote == True:
        action_runner.run_remote_synthesis()
    elif options.make == True:
        action_runner.generate_modelsim_makefile()
    elif options.ise_proj == True:
        action_runner.generate_ise_project(top_mod=tm)
    elif options.make_fetch == True:
        action_runner.generate_fetch_makefile()

if __name__ == "__main__":
    main()
