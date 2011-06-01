#!/usr/bin/python
# -*- coding: utf-8 -*-

import global_mod
import time
import os
import sys
import pprint as prettyprinter

def rawprint(msg):
    print(msg)

def echo(msg):
    print(("["+os.path.basename(sys.argv[0]) + " " + "%.5f" % (time.time()-global_mod.t0) + "]: " + str(msg)))

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