#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 Pawel Szostek (pawel.szostek@cern.ch)
#
#    This source code is free software; you can redistribute it
#    and/or modify it in source code form under the terms of the GNU
#    General Public License as published by the Free Software
#    Foundation; either version 2 of the License, or (at your option)
#    any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA
#


import time
import os
from connection import Connection
import global_mod
import msg as p
import optparse
from module import Module
from fetch import ModulePool

def main():
    global_mod.t0 = time.time()

    parser = optparse.OptionParser()

    parser.add_option("--manifest-help", action="store_true",
    dest="manifest_help", help="print manifest file variables description")

    parser.add_option("--make-sim", dest="make_sim", action="store_true",
    default=None, help="generate a simulation Makefile")

    parser.add_option("--make-fetch", dest="make_fetch", action="store_true",
    default=None, help="generate a makefile for modules' fetching")

    parser.add_option("--make-ise", dest="make_ise", action="store_true",
    default=None, help="generate a makefile for local ISE synthesis")

    parser.add_option("--make-remote", dest="make_remote", action="store_true",
    default=None, help="generate a makefile for remote synthesis")

    parser.add_option("-f", "--fetch", action="store_true", dest="fetch",
    help="fetch and/or update remote modules listed in Manifet")

    parser.add_option("--clean", action="store_true", dest="clean",
    help="remove all modules fetched for this one")

    parser.add_option("--ise-proj", action="store_true", dest="ise_proj",
    help="create/update an ise project including list of project files")

    parser.add_option("-l", "--synthesize-locally", dest="local",
    action="store_true", help="perform a local synthesis")

    parser.add_option("-r", "--synthesize-remotelly", dest="remote",
    action="store_true", help="perform a remote synthesis")

    parser.add_option("--synth-server", dest="synth_server",
    default=None, help="use given SERVER for remote synthesis", metavar="SERVER")

    parser.add_option("--synth-user", dest="synth_user",
    default=None, help="use given USER for remote synthesis", metavar="USER")

    parser.add_option("--py", dest="arbitrary_code",
    default="", help="add arbitrary code to all manifests' evaluation")

    parser.add_option("-v", "--verbose", dest="verbose", action="store_true",
    default="false", help="verbose mode")

    (options, args) = parser.parse_args()
    global_mod.options = options

    if options.manifest_help == True:
        from helper_classes import ManifestParser
        ManifestParser().help()
        quit()

    p.vprint("LoadTopManifest");
    pool = ModulePool()
    m = Module(parent=None, url=os.getcwd(), source="local", fetchto=".", pool=pool )
    pool.set_top_module(m)

    if m.manifest == None:
        p.echo("No manifest found. At least an empty one is needed")
        quit()
    global_mod.top_module = m
    global_mod.top_module.parse_manifest()

    global_mod.global_target = global_mod.top_module.target

    global_mod.ssh = Connection(ssh_user=options.synth_user, ssh_server=options.synth_server)

    ssh = global_mod.ssh
    from hdlmake_kernel import HdlmakeKernel
    kernel = HdlmakeKernel(modules_pool=pool, connection=ssh)

    if options.fetch == True:
        kernel.fetch()
    elif options.local == True:
        kernel.run_local_synthesis()
    elif options.remote == True:
        kernel.run_remote_synthesis()
    elif options.make_sim == True:
        kernel.generate_modelsim_makefile()
    elif options.ise_proj == True:
        kernel.generate_ise_project()
    elif options.make_fetch == True:
        kernel.generate_fetch_makefile()
    elif options.make_ise == True:
        kernel.generate_ise_makefile()
    elif options.make_remote == True:
        kernel.generate_remote_synthesis_makefile()
    elif options.clean == True:
        kernel.clean_modules()
    else:
        p.echo("Running automatic flow")
        kernel.run()

if __name__ == "__main__":
    main()
