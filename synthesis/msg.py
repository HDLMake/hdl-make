#!/usr/bin/python
# -*- coding: utf-8 -*-

import global_mod
import time
import os
import sys

def my_msg(msg):
    print "["+os.path.basename(sys.argv[0]) + " " + "%.5f" % (time.time()-global_mod.t0) + "]: " + msg
def v_msg(msg):
    if global_mod.options.verbose == True:
        my_msg(msg)