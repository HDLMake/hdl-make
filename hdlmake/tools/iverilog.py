#!/usr/bin/env python

from subprocess import Popen, PIPE

IVERILOG_STARDAND_LIBS = ['std', 'ieee', 'ieee_proposed', 'vl', 'synopsys',
                      'simprim', 'unisim', 'unimacro', 'aim', 'cpld',
                      'pls', 'xilinxcorelib', 'aim_ver', 'cpld_ver',
                      'simprims_ver', 'unisims_ver', 'uni9000_ver',
                      'unimacro_ver', 'xilinxcorelib_ver', 'secureip']

def detect_iverilog_version(path):
    iverilog = Popen("iverilog -v 2>/dev/null| awk '{if(NR==1) print $4}'",
                     shell=True,
                     stdin=PIPE,
                     stdout=PIPE,
                     close_fds=True)
    version = iverilog.stdout.readlines()[0].strip()
    return version
