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


import global_mod
import time
import os
import sys
import pprint as prettyprinter

t0 = time.time()

def printhr():
    rawprint("------------------")

def rawprint(msg = ""):
    print(msg)

def warning(msg):
    rawprint("WARNING: " + msg)

def info(msg):
    rawprint("INFO:    " + msg)

def error(msg):
    rawprint("ERROR:   " + msg)

def echo(msg):
    global t0
    print(("["+os.path.basename(sys.argv[0]) + " " + "%.5f" % (time.time()-t0) + "]: " + str(msg)))

def vprint(msg):
    if global_mod.options.verbose == True:
        echo(msg)

def pprint(msg):
    pp = prettyprinter.PrettyPrinter(indent = 2)
    pp.pprint(msg)

def vpprint(msg):
    if global_mod.options.verbose == True:
        pp = prettyprinter.PrettyPrinter(indent = 2)
        pp.pprint(msg)