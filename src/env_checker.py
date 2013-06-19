#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)

import os
import sys
import msg as p


class EnvChecker(dict):
    def __init__(self, options, manifest):
        self.options = options
        self.manifest = manifest

    def check(self):
        platform = sys.platform
        print("Platform: %s" % platform)

        xilinx = os.environ.get("XILINX")
        self.report_in_path("ise")
        if xilinx:
            print("Environmental variable %s is set: %s." % ("XILINX", xilinx))
            self["xilinx"] = xilinx
        else:
            print("Environmental variable XILINX is not set.")
        try:
            ise_version = tuple(self.manifest["force_ise"].esplit('.'))
        except KeyError:
            ise_version = None

        if ise_version is None:
            ise_version = self._guess_ise_version(xilinx, '')

        if ise_version is not None:
            print("ISE version: %d.%d" % (ise_version[0], ise_version[1]))
        else:
            print("ISE version could not be determined")
        top_module = self.report_and_set_var("TOP_MODULE")

        self.report_in_path("isim")
        self.report_and_set_var("ise_path")
        self.report_in_path("vsim")
        self.report_and_set_var("modelsim_path")
        self.report_in_path("iverilog")

        self.report_and_set_var("coredir")

        self.report_and_set_var("rsynth_user")
        self.report_and_set_var("rsynth_ise_path")
        self.report_and_set_var("rsynth_use_screen")

    def check_modelsim_ini(self):
        pass

    def check_xilinxsim_init(self):
        pass

    def _guess_ise_version(self, xilinx, ise_path):
        import subprocess
        import re
        xst = subprocess.Popen('which xst', shell=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
        lines = xst.stdout.readlines()
        if not lines:
            return None

        xst = str(lines[0].strip())
        version_pattern = re.compile(".*?(\d\d\.\d).*") #First check if we have version in path
        match = re.match(version_pattern, xst)
        if match:
            ise_version = match.group(1)
        else: #If it is not the case call the "xst -h" to get version
            xst_output = subprocess.Popen('xst -h', shell=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
            xst_output = xst_output.stdout.readlines()[0]
            xst_output = xst_output.strip()
            version_pattern = \
                    re.compile('Release\s(?P<major>\d|\d\d)[^\d](?P<minor>\d|\d\d)\s.*')
            match = re.match(version_pattern, xst_output)
            if match:
                ise_version = ''.join((match.group('major'), '.', match.group('minor')))
            else:
                p.error("xst output is not in expected format: "+ xst_output +"\n"
                        "Can't determine ISE version")
                return None

        p.vprint("ISE version: " + ise_version)
        return ise_version

    def __figure_out_ise_path(self):
        if self.options.force_ise is not None:
            if self.options.force_ise == 0:
                ise = self.__check_ise_version()
            else:
                ise = self.options.force_ise
        else:
            ise = 0

        try:
            ise_path = path.ise_path_32[str(ise)]+'/'
        except KeyError:
            if ise != 0:
                ise_path = "/opt/Xilinx/"+str(ise)+"/ISE_DS/ISE/bin/lin/"
            else:
                ise_path = ""
        return ise_path

    def _get(self, name):
        assert not name.startswith("HDLMAKE_")
        assert isinstance(name, basestring)

        return os.environ.get("HDLMAKE_%s" % name)

    def get_path(self, name):
        return os.popen("which %s" % name).read().strip()

    def check_in_path(self, name):
        assert isinstance(name, basestring)

        path = self.get_path(name)
        return len(path) > 0

    def report_in_path(self, name):
        path = self.get_path(name)
        if path:
            print("%s is in PATH: %s." % (name, path))
        else:
            print("%s is not in PATH." % name)

    def report_and_set_var(self, name):
        name = name.upper()
        val = os.environ.get("HDLMAKE_%s" % name)
        if val:
            print("Environmental variable HDLMAKE_%s is set: %s." % (name, val))
            self[name.lower()] = val
        else:
            print("Environmental variable HDLMAKE_%s is not set." % name)

if __name__ == "__main__":
    ec = EnvChecker({}, {})
    ec.check()