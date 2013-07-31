#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Modified to allow ISim simulation by Lucas Russo (lucas.russo@lnls.br)

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
    make_sim = subparsers.add_parser("make-sim", help="generate a simulation Makefile")
    make_sim.add_argument("--append", help="append generated makefile to the existing one", default=False, action="store_true")
    make_fetch = subparsers.add_parser("make-fetch", help="generate a makefile for modules' fetching")
    make_fetch.add_argument("--append", help="append generated makefile to the existing one", default=False, action="store_true")
    make_ise = subparsers.add_parser("make-ise", help="generate a makefile for local ISE synthesis")
    make_ise.add_argument("--append", help="append generated makefile to the existing one", default=False, action="store_true")
    make_remote = subparsers.add_parser("make-remote", help="generate a makefile for remote synthesis")
    make_remote.add_argument("--append", help="append generated makefile to the existing one", default=False, action="store_true")
    fetch = subparsers.add_parser("fetch", help="fetch and/or update remote modules listed in Manifest")
    clean = subparsers.add_parser("clean", help="remove all modules fetched for this one")
    listmod = subparsers.add_parser("list-mods", help="List all modules together with their files")
    listfiles = subparsers.add_parser("list-files", help="List all files in a form of a space-separated string")
    listfiles.add_argument("--delimiter", help="set delimitier for the list of files", dest="delimiter", default=' ')
    merge_cores = subparsers.add_parser("merge-cores", help="Merges entire synthesizable content of an project into a pair of VHDL/Verilog files")
    merge_cores.add_argument("--dest", help="name for output merged file", dest="dest", default=None)
    ise_proj = subparsers.add_parser("ise-proj", help="create/update an ise project including list of project")
    quartus_proj = subparsers.add_parser("quartus-proj", help="create/update a quartus project including list of project")
    version = subparsers.add_parser("version", help="print version id of this Hdlmake build")

    parser.add_argument("--py", dest="arbitrary_code",
                        default="", help="add arbitrary code to all manifests' evaluation")

    parser.add_argument("--log", dest="log",
                        default="info", help="set logging level (one of debug, info, warning, error, critical")

    options = parser.parse_args()
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
    global_mod.top_module = modules_pool.get_top_module()

    global_mod.global_target = global_mod.top_module.target
    global_mod.mod_pool = modules_pool
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

    if options.command == "manifest-help":
        ManifestParser().print_help()
        quit()
    elif options.command == "make-sim":
        action = GenerateSimulationMakefile
    elif options.command == "make-fetch":
        action = GenerateFetchMakefile
    elif options.command == "make-ise":
        action = GenerateISEMakefile
    elif options.command == "make-remote":
        action = GenerateRemoteSynthesisMakefile
    elif options.command == "fetch":
        action = FetchModules
    elif options.command == "clean":
        action = CleanModules
    elif options.command == "list-mods":
        action = ListModules
    elif options.command == "list-files":
        action = ListFiles
    elif options.command == "merge-cores":
        action = MergeCores
    elif options.command == "ise-proj":
        action = GenerateISEProject
    elif options.command == "quartus-proj":
        action = GenerateQuartusProject
    elif options.command == "version":
        print("Hdlmake build " + BUILD_ID)
        quit()

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
