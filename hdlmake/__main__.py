#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 - 2015 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Multi-tool support by Javier D. Garcia-Lasheras (javier@garcialasheras.com)
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
import importlib
import argparse
import logging
import sys

from .util.termcolor import colored
from .manifest_parser import ManifestParser
from .module_pool import ModulePool
from . import fetch as fetch_mod
from ._version import __version__


def main():
    """This is the main function, where HDLMake starts.
    Here, we make the next processes:
        -- parse command
        -- check and set the environment
        -- prepare the global module containing the heavy common stuff
    """

    #
    # SET & GET PARSER
    #
    parser = _get_parser()

    #
    # PARSE & GET OPTIONS
    #
    options = _get_options(sys, parser)

    # Here we set the log level (A.K.A.) debug verbosity)
    numeric_level = getattr(logging, options.log.upper(), None)
    if not isinstance(numeric_level, int):
        sys.exit('Invalid log level: %s' % options.log)

    logging.basicConfig(
        format=colored(
            "%(levelname)s",
            "yellow") + colored(
            "\t%(filename)s:%(lineno)d: %(funcName)s()\t",
            "blue") + "%(message)s",
        level=numeric_level)
    logging.debug(str(options))

    # Create a ModulePool object, this will become our workspace
    modules_pool = ModulePool()

    # Set the module_pool environment by providing the options: this is a must!
    modules_pool.set_environment(options)

    # Now, we add the first module, the one from which we are launching the program:
    # Note that we are asking for not processing the manifest and specifying
    # that there is not a parent module.
    # 1- Hdlmake create a new Module() object
    # 2- There is not a top_module yet in modules_pool, so only this time...:
    #    - this becomes the top_module
    #    - the manifest is parsed & processed
    # And dependent modules are added to the modules pool, but...
    # .. How should we handle recursive fetching?
    # Note: CERN BE-CO-HT advocates for defaulting to non-recursive.

    modules_pool.new_module(parent=None,
                            url=os.getcwd(),
                            source=fetch_mod.LOCAL,
                            fetchto=".")

    # Check if our top_module has been successfully assigned and
    # contains a Manifest.py (ModulePool class)
    # if not modules_pool.get_top_module().manifest_dict:
    #    logging.info("No manifest found. At least an empty one is needed")
    #    logging.info("To see some help, type hdlmake --help")
    #    sys.exit("Exiting")
    _action_runner(modules_pool)


def _action_runner(modules_pool):

    #
    # DECODE THE COMMANDS/ACTIONS HERE  #
    #
    top_mod = modules_pool.get_top_module()
    options = modules_pool.env.options

    if options.command == "check-env":
        modules_pool.env.check_env(verbose=True)
        quit()
    elif options.command == "manifest-help":
        ManifestParser().print_help()
        quit()
    elif options.command == "auto":
        logging.info("Running automatic flow.")
        if not top_mod.action:
            logging.error("`action' manifest variable has to be specified. "
                          "Otherwise hdlmake doesn't know how to handle the project.")
            quit()
        if top_mod.action == "simulation":
            modules_pool.simulation_makefile()
        elif top_mod.action == "synthesis":
            modules_pool.synthesis_project()
            #modules_pool.synthesis_makefile()
        elif top_mod.action == "qsys_hw_tcl_update":
            if not top_mod.manifest_dict["hw_tcl_filename"]:
                logging.error("'hw_tcl_filename' manifest variable has to be specified. "
                              "Otherwise hdlmake doesn't know which file to update.")
                quit()
            modules_pool.qsys_hw_tcl_update()
    elif options.command == "make-simulation":
        modules_pool.simulation_makefile()
    elif options.command == "make-synthesis":
        modules_pool.synthesis_makefile()
    elif options.command == "fetch":
        modules_pool.fetch()
    elif options.command == "clean":
        modules_pool.clean()
    elif options.command == "list-mods":
        modules_pool.list_modules()
    elif options.command == "list-files":
        modules_pool.list_files()
    elif options.command == "merge-cores":
        modules_pool.merge_cores()
    elif options.command == "project":
        modules_pool.synthesis_project()
    elif options.command == "tree":
        modules_pool.generate_tree()


def _get_parser():
    """This is the parser function, where options and commands are defined.
    Here, we make the next processes:
    """

    usage = """hdlmake [command] [options]"""
    description = """Version %s\n
        To see optional arguments for particular command type:
        hdlmake <command> --help
\0
""" % (__version__,)

    parser = argparse.ArgumentParser("hdlmake",
                                     usage=usage,
                                     description=description)
    subparsers = parser.add_subparsers(title="commands", dest="command")

    check_env = subparsers.add_parser("check-env",
                                      help="check environment for HDLMAKE-related settings",
                                      description="Look for environmental variables specific for HDLMAKE.\n"
                                                  "Hdlmake will examine presence of supported synthesis and simulation"
                                                  "tools.\n")
    manifest_help = subparsers.add_parser(
        "manifest-help",
        help="print manifest file variables description")
    make_simulation = subparsers.add_parser(
        "make-simulation",
        help="generate simulation makefile")
    make_synthesis = subparsers.add_parser(
        "make-synthesis",
        help="generate synthesis makefile")

    fetch = subparsers.add_parser(
        "fetch",
        help="fetch and/or update remote modules listed in Manifest")
    clean = subparsers.add_parser(
        "clean",
        help="remove all modules fetched for direct and indirect children of this module")
    listmod = subparsers.add_parser(
        "list-mods",
        help="List all modules together with their files")
    listmod.add_argument(
        "--with-files",
        help="list modules together with their files",
        default=False,
        action="store_true",
        dest="withfiles")
    listmod.add_argument(
        "--terse",
        help="do not print comments",
        default=False,
        action="store_true",
        dest="terse")
    listfiles = subparsers.add_parser(
        "list-files",
        help="List all files in a form of a space-separated string")
    listfiles.add_argument(
        "--delimiter",
        help="set delimitier for the list of files",
        dest="delimiter",
        default=None)
    # listfiles.add_argument("--reverse", help="reverse the order for the list
    # of files", dest="reverse", default=False, action="store_true")
    merge_cores = subparsers.add_parser(
        "merge-cores",
        help="Merges entire synthesizable content of an project into a pair of VHDL/Verilog files")
    merge_cores.add_argument(
        "--dest",
        help="name for output merged file",
        dest="dest",
        default=None)
    synthesis_proj = subparsers.add_parser(
        "project",
        help="create/update a project for the appropriated tool")
    tree = subparsers.add_parser(
        "tree",
        help="generate a module hierarchy tree")
    tree.add_argument(
        "--with-files",
        help="Add files to the module hierarchy tree",
        default=False,
        action="store_true",
        dest="withfiles")
    tree.add_argument(
        "--graphviz",
        dest="graphviz",
        default=None,
        help="Activate graphviz and specify the program to be used to plot the graph (twopi, gvcolor, wc, ccomps, tred, sccmap, fdp, circo, neato, acyclic, nop, gvpr, dot, sfdp)")
    tree.add_argument(
        "--web",
        help="Edit the tree hierarchy in a web browser",
        default=False,
        action="store_true",
        dest="web")
    tree.add_argument(
        "--solved",
        help="Enable the parser",
        default=False,
        action="store_true",
        dest="solved")
    condition_check = argparse.ArgumentParser()
    condition_check.add_argument("--tool", dest="tool", required=True)
    condition_check.add_argument(
        "--reference",
        dest="reference",
        required=True)
    condition_check.add_argument(
        "--condition",
        dest="condition",
        required=True)

    auto = subparsers.add_parser(
        "auto",
        help="default action for hdlmake. Run when no args are given")
    auto.add_argument(
        '-v',
        '--version',
        action='version',
        version=parser.prog +
        " " +
        __version__)
    auto.add_argument(
        "--force",
        help="force hdlmake to generate the makefile, even if the specified tool is missing",
        default=False,
        action="store_true")
    auto.add_argument(
        "--noprune",
        help="prevent hdlmake from pruning unneeded files",
        default=False,
        action="store_true")

    parser.add_argument("--py", dest="arbitrary_code",
                        default="", help="add arbitrary code when evaluation all manifests")

    parser.add_argument("--log", dest="log",
                        default="info", help="set logging level (one of debug, info, warning, error, critical)")
    parser.add_argument(
        "--generate-project-vhd", help="generate project.vhd file with a meta package describing the project",
        dest="generate_project_vhd", default=False, action="store_true")
    parser.add_argument(
        "--force",
        help="force hdlmake to generate the makefile, even if the specified tool is missing",
        default=False,
        action="store_true")

    return parser


def _get_options(sys, parser):
    options = None
    if len(sys.argv[1:]) == 0:
            options = parser.parse_args(['auto'])

    elif len(sys.argv[1:]) == 1:
        if sys.argv[1] == "_conditioncheck":
            options = condition_check.parse_args(sys.argv[2:])
            env = Env(options)
            env.check_env()
            CheckCondition(modules_pool=None,
                           options=options,
                           env=env).run()
            quit()
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            options = parser.parse_args(sys.argv[1:])
        elif sys.argv[1].startswith('-'):
            options = parser.parse_args(["auto"] + sys.argv[1:])
        else:
            options = parser.parse_args(sys.argv[1:])
    else:
        options = parser.parse_args(sys.argv[1:])
    return options


if __name__ == "__main__":
    main()
