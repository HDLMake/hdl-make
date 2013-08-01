#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
#
# This file is part of Hdlmake.
#
# Hdlmake is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hdlmake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Hdlmake.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import print_function
import os
import global_mod
import argparse
import logging
import sys
from manifest_parser import ManifestParser
from module_pool import ModulePool
from env import Env
from action import (CleanModules, FetchModules, GenerateFetchMakefile,
                    GenerateISEMakefile, GenerateISEProject, ListFiles,
                    ListModules, MergeCores, GenerateQuartusProject,
                    GenerateRemoteSynthesisMakefile, GenerateSimulationMakefile)
try:
    from build_hash import BUILD_ID
except:
    BUILD_ID = "unrecognized"


def main():
    parser = argparse.ArgumentParser("hdlmake")
    subparsers = parser.add_subparsers(title="commands", dest="command")

    check_env = subparsers.add_parser("check-env", help="check environment for HDLMAKE-related settings")
    check_manifest = subparsers.add_parser("check-manifest", help="check manifest for formal correctness")
    check_manifest.add_argument("--top", help="indicate path to the top manifest", default=None)
    manifest_help = subparsers.add_parser("manifest-help", help="print manifest file variables description")
    auto = subparsers.add_parser("auto", help="default action for hdlmake. Run when no args are given")
    fetch = subparsers.add_parser("fetch", help="fetch and/or update remote modules listed in Manifest")
    fetch.add_argument("--flatten", help="`flatten' modules' hierarchy by storing everything in top module's fetchto direactoru",
                       default=False, action="store_true")
    fetch.add_argument("--update", help="force updating of the fetched modules", default=False, action="store_true")
    clean = subparsers.add_parser("clean", help="remove all modules fetched for this one")
    listmod = subparsers.add_parser("list-mods", help="List all modules together with their files")
    listmod.add_argument("--with-files", help="list modules together with their files", default=False, action="store_true", dest="withfiles")
    listfiles = subparsers.add_parser("list-files", help="List all files in a form of a space-separated string")
    listfiles.add_argument("--delimiter", help="set delimitier for the list of files", dest="delimiter", default=' ')
    merge_cores = subparsers.add_parser("merge-cores", help="Merges entire synthesizable content of an project into a pair of VHDL/Verilog files")
    merge_cores.add_argument("--dest", help="name for output merged file", dest="dest", default=None)
    ise_proj = subparsers.add_parser("ise-project", help="create/update an ise project including list of project")
    quartus_proj = subparsers.add_parser("quartus-project", help="create/update a quartus project including list of project")
    # version = subparsers.add_parser("version", help="print version id of this Hdlmake build")

    parser.add_argument("--py", dest="arbitrary_code",
                        default="", help="add arbitrary code to all manifests' evaluation")

    parser.add_argument("--log", dest="log",
                        default="info", help="set logging level (one of debug, info, warning, error, critical")

    if len(sys.argv) < 2:
        options = parser.parse_args(['auto'])
    else:
        options = parser.parse_args(sys.argv[1:])
    global_mod.options = options

    numeric_level = getattr(logging, options.log.upper(), None)
    if not isinstance(numeric_level, int):
        sys.exit('Invalid log level: %s' % options.log)

    logging.basicConfig(format="%(levelname)s %(funcName)s() %(filename)s:%(lineno)d: %(message)s", level=numeric_level)
    logging.debug(str(options))

    modules_pool = ModulePool()
    modules_pool.new_module(parent=None, url=os.getcwd(), source="local",
                            fetchto=".", process_manifest=False)

    # Setting top_module as top module of design (ModulePool class)
    if modules_pool.get_top_module().manifest is None:
        logging.info("No manifest found. At least an empty one is needed")
        logging.info("To see some help, type hdlmake --help")
        sys.exit("Exiting")

    # Setting global variable (global_mod.py)
    top_mod = modules_pool.get_top_module()
    global_mod.top_module = top_mod

    global_mod.global_target = global_mod.top_module.target
    global_mod.mod_pool = modules_pool

    # if options.command == "version":
    #     print("Hdlmake build " + BUILD_ID)
    #     quit()

    env = Env(options)
    global_mod.env = env
    if options.command == "check-env":
        env.check_env(verbose=True)
        quit()
    if options.command == "check-manifest":
        env.check_manifest(modules_pool.get_top_module().manifest, verbose=True)

    modules_pool.process_top_module_manifest()

    env.top_module = modules_pool.get_top_module()
    env.check_env(verbose=False)
    env.check_env_wrt_manifest(verbose=False)

    if options.command == "auto":
        logging.info("Running automatic flow.")
        if top_mod.action == "simulation":
            sim = GenerateSimulationMakefile(modules_pool=modules_pool, options=options, env=env)
            sim.run()
            quit()
        elif top_mod.action == "synthesis":
            syn = GenerateISEMakefile(modules_pool=modules_pool, options=options, env=env)
            ise = GenerateISEProject(modules_pool=modules_pool, options=options, env=env)
            remote = GenerateRemoteSynthesisMakefile(modules_pool=modules_pool, options=options, env=env)
            syn.run()
            ise.run()
            remote.run()
            quit()

    if options.command == "manifest-help":
        ManifestParser().print_help()
        quit()
    elif options.command == "make-simulation":
        action = GenerateSimulationMakefile
    elif options.command == "make-fetch":
        action = GenerateFetchMakefile
    elif options.command == "make-ise":
        action = GenerateISEMakefile
    elif options.command == "make-remote":
        action = GenerateRemoteSynthesisMakefile
    elif options.command == "fetch":
        action = FetchModules
    elif options.command == "ise-project":
        action = GenerateISEProject
    elif options.command == "clean":
        action = CleanModules
    elif options.command == "list-mods":
        action = ListModules
    elif options.command == "list-files":
        action = ListFiles
    elif options.command == "merge-cores":
        action = MergeCores

    elif options.command == "quartus-project":
        action = GenerateQuartusProject


    action_instance = action(modules_pool=modules_pool, options=options, env=env)

    try:
        action_instance.run()
    except Exception as e:
        import traceback
        logging.error(e)
        print("Trace:")
        traceback.print_exc()

if __name__ == "__main__":
    main()
