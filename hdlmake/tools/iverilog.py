#!/usr/bin/env python

from subprocess import Popen, PIPE


def detect_iverilog_version(path):
    iverilog = Popen("iverilog -v 2>/dev/null| awk '{if(NR==1) print $4}'",
                     shell=True,
                     stdin=PIPE,
                     stdout=PIPE,
                     close_fds=True)
    version = iverilog.stdout.readlines()[0].strip()
    return version
