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

"""This is the entry point for HDLMake working in command line app mode"""

from __future__ import print_function
from __future__ import absolute_import
import argparse
import sys

from .manifest_parser import ManifestParser
from .module_pool import ModulePool
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

    # Create a ModulePool object, this will become our workspace
    modules_pool = ModulePool(options)

    # Execute the appropriated action for the freshly created modules pool
    _action_runner(modules_pool)


def _action_runner(modules_pool):
    """Funtion that decodes and executed the action selected by the user"""
    options = modules_pool.options
    if options.command == "manifest-help":
        ManifestParser().print_help()
        quit()
    elif options.command == "makefile":
        modules_pool.makefile()
    elif options.command == "fetch":
        modules_pool.fetch()
    elif options.command == "clean":
        modules_pool.clean()
    elif options.command == "list-mods":
        modules_pool.list_modules()
    elif options.command == "list-files":
        modules_pool.list_files()
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
    subparsers.add_parser(
        "manifest-help",
        help="print manifest file variables description")
    subparsers.add_parser(
        "fetch",
        help="fetch and/or update all of the remote modules")
    subparsers.add_parser(
        "clean",
        help="clean all of the already fetched remote modules")
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
        help="List all of the files in the design hierarchy")
    listfiles.add_argument(
        "--delimiter",
        help="set delimitier for the list of files",
        dest="delimiter",
        default=None)
    listfiles.add_argument(
        "--reverse",
        help="reverse the order for the list of files",
        dest="reverse",
        default=False,
        action="store_true")
    listfiles.add_argument(
        "--top",
        help="print only those files required to build 'top'",
        dest="top",
        default=None)
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
        help="Activate graphviz and specify the program to be used to plot "
             "the graph (twopi, gvcolor, wc, ccomps, tred, sccmap, fdp, "
             "circo, neato, acyclic, nop, gvpr, dot, sfdp)")
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
    makefile = subparsers.add_parser(
        "makefile",
        help="Write the Makefile -- default action for hdlmake.")
    makefile.add_argument(
        '-v',
        '--version',
        action='version',
        version=parser.prog +
        " " +
        __version__)
    makefile.add_argument(
        "--noprune",
        help="prevent hdlmake from pruning unneeded files",
        default=False,
        action="store_true")
    parser.add_argument(
        "-f", "--filename",
        help="Name for the Makefile file to be created",
        default=None,
        dest="filename")
    parser.add_argument(
        "-p", "--prefix",
        dest="prefix_code",
        default="",
        help="Arbitrary python code to be executed just before the Manifest")
    parser.add_argument(
        "-s", "--sufix",
        dest="sufix_code",
        default="",
        help="Arbitrary python code to be executed just after the Manifest")
    parser.add_argument(
        "--log",
        dest="log",
        default="info",
        help="set logging level: debug, info, warning, error, critical")
    return parser


def _get_options(sys_aux, parser):
    """Function that decodes and set the provided command user options"""
    options = None
    if len(sys_aux.argv[1:]) == 0:
        options = parser.parse_args(['makefile'])
    elif len(sys_aux.argv[1:]) == 1:
        if sys_aux.argv[1] == "--help" or sys_aux.argv[1] == "-h":
            options = parser.parse_args(sys_aux.argv[1:])
        elif sys_aux.argv[1].startswith('-'):
            options = parser.parse_args(["makefile"] + sys_aux.argv[1:])
        else:
            options = parser.parse_args(sys_aux.argv[1:])
    elif len(sys_aux.argv[1:]) % 2 == 0:
        options = parser.parse_args(sys_aux.argv[1:] + ["makefile"])
    else:
        options = parser.parse_args(sys_aux.argv[1:])
    return options


if __name__ == "__main__":
    main()
