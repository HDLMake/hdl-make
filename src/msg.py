#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)


import global_mod
try:
  from build_hash import BUILD_ID
except:
  BUILD_ID = "unrecognized"
import time
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
    rawprint(msg)

def vprint(msg):
    if global_mod.options.verbose is True:
        echo(msg)

def pprint(msg):
    pp = prettyprinter.PrettyPrinter(indent = 2)
    pp.pprint(msg)

def vpprint(msg):
    if global_mod.options.verbose is True:
        pp = prettyprinter.PrettyPrinter(indent = 2)
        pp.pprint(msg)

def print_version():
    rawprint("Hdlmake build " + BUILD_ID)

def print_action_help():
    rawprint("`Action' variable was not specified")
    rawprint("Allowed values are: \"simulation\" or \"synthesis\"")
    rawprint()
    rawprint("This variable in a manifest file is necessary for Hdlmake " \
    "to be able to know what to do with the given modules' structure.")
    basic()

def basic():
    rawprint("For more help type `hdlmake --help' "\
    "or visit http://www.ohwr.org/projects/hdl-make")
