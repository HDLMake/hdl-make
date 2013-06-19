#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)

import os
import sys
import msg as p
from subprocess import Popen, PIPE
import re


class _IsePath(object):
    _ise_path_64 = {
        10: {0: "/opt/Xilinx/10.0/ISE/bin/lin",
             1: "/opt/Xilinx/10.1/ISE/bin/lin"},
        12: {1: "/opt/Xilinx/12.1/ISE_DS/ISE/bin/lin",
             2: "/opt/Xilinx/12.2/ISE_DS/ISE/bin/lin64",
             4: "/opt/Xilinx/12.4/ISE_DS/ISE/bin/lin64"},
        13: {1: "/opt/Xilinx/13.1/ISE_DS/ISE/bin/lin64"}
    }

    _ise_path_64 = {
        10: {0: "/opt/Xilinx/10.0/ISE/bin/lin",
             1: "/opt/Xilinx/10.1/ISE/bin/lin"},
        12: {1: "/opt/Xilinx/12.1/ISE_DS/ISE/bin/lin",
             2: "/opt/Xilinx/12.2/ISE_DS/ISE/bin/lin64",
             4: "/opt/Xilinx/12.4/ISE_DS/ISE/bin/lin64"},
        13: {1: "/opt/Xilinx/13.1/ISE_DS/ISE/bin/lin64"}
    }

    @staticmethod
    def get_path(arch, major, minor):
        if arch == 32:
            dct = _IsePath._ise_path_32
        else:
            dct = _IsePath._ise_path_64

        try:
            minor_dct = dct[major]
            try:
                path = minor_dct[minor]
                return path
            except KeyError:
                #get latest for the chosen major version
                minor_keys = sorted(minor_dct.keys())
                max_minor_key = minor_keys[-1]
                path = minor_dct[max_minor_key]

        except KeyError:
            #get path for the latest version from the dict
            major_keys = sorted(dct.keys())
            max_major_key = major_keys[-1]
            minor_dct = dct[max_major_key]
            minor_keys = sorted(minor_dct.keys())
            max_minor_key = minor_keys[-1]
            path = minor_dct[max_minor_key]
            return path


class EnvChecker(dict):
    def __init__(self, options, manifest):
        self.options = options
        self.manifest = manifest

    def check(self):
        platform = sys.platform
        print("Platform: %s" % platform)

        #1: determine path for ise

        xilinx = os.environ.get("XILINX")
        if xilinx:
            print("Environmental variable %s is set: %s." % ("XILINX", xilinx))
            self["xilinx"] = xilinx
        else:
            print("Environmental variable XILINX is not set.")

        self.report_and_set_var("ise_path")
        if "ise_path" in self and "xilinx" in self:
            print("HDLMAKE_ISE_PATH and XILINX can't be set at a time\n"
                  "Ignoring HDLMAKE_ISE_PATH")
            self["ise_path"] = self["xilinx"]

        if "ise_path" in self:
            if self.check_in_path("ise", self["ise_path"]):
                print("ISE found in HDLMAKE_ISE_PATH: %s." % self["ise_path"])
            else:
                print("ISE not found in HDLMAKE_ISE_PATH: %s." % self("ise_path"))
        else:
            if self.check_in_path("ise"):
                print("ISE found in PATH: %s." % self.get_path("ise"))
            else:
                print("ISE not found in PATH")

        #2: determine ISE version
        try:
            ise_version = tuple(self.manifest["force_ise"].split('.'))
            print("ise_version set in the manifest: %d.%d" % (ise_version[0], ise_version[1]))
            self["ise_version"] = ise_version
        except KeyError:
            ise_version = None

        if "ise_version" not in self:
            ise_version = self._guess_ise_version(xilinx, '')
            if ise_version:
                print("force_ise not set in the manifest,"
                      " guessed ISE version: %d.%d" % (ise_version[0], ise_version[1]))
            self["ise_version"] = ise_version

            #######
        self.report_and_set_var("top_module")

        self.report_in_path("isim")

        #3: determine modelsim path
        self.report_and_set_var("modelsim_path")
        if "modelsim_path" in self:
            if not self.check_in_path("vsim", self["modelsim_path"]):
                if self.report_in_path("vsim"):
                    self["modelsim_path"] = self.get_path("modelsim_path")

        #4: determine iverilog path
        self.report_in_path("iverilog")
        if "iverilog" in self:
            if not self.check_in_path("iverilog", self["iverilog_path"]):
                if self.report_in_path("iverilog"):
                    self["iverilog_path"] = self.get_path("iverilog")

        self.report_and_set_var("coredir")

        self.report_and_set_var("rsynth_user")
        self.report_and_set_var("rsynth_ise_path")
        self.report_and_set_var("rsynth_use_screen")

    def check_xilinxsim_init(self):
        pass

    def _guess_ise_version(self, xilinx, ise_path):
        xst = Popen('which xst', shell=True, stdin=PIPE,
                    stdout=PIPE, close_fds=True)
        lines = xst.stdout.readlines()
        if not lines:
            return None

        xst = str(lines[0].strip())
        version_pattern = re.compile('.*?(?P<major>\d|\d\d)[^\d](?P<minor>\d|\d\d).*')
        # First check if we have version in path

        match = re.match(version_pattern, xst)
        if match:
            ise_version = (int(match.group('major')), int(match.group('minor')))
        else:  # If it is not the case call the "xst -h" to get version
            xst_output = Popen('xst -h', shell=True, stdin=PIPE,
                               stdout=PIPE, close_fds=True)
            xst_output = xst_output.stdout.readlines()[0]
            xst_output = xst_output.strip()
            version_pattern = re.compile('Release\s(?P<major>\d|\d\d)[^\d](?P<minor>\d|\d\d)\s.*')
            match = re.match(version_pattern, xst_output)
            if match:
                ise_version = (int(match.group('major')), int(match.group('minor')))
            else:
                p.error("xst output is not in expected format: %s\n" % xst_output +
                        "Can't determine ISE version")
                return None

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
            #TODO: change hardcoded 32
            ise_path = _IsePath.get_path(arch=32, major=ise[0], minor=ise[1]) + '/'
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

    def check_in_path(self, name, path=None):
        if path is not None:
            return os.path.exists(os.path.join(path, name))
        else:
            assert isinstance(name, basestring)

            path = self.get_path(name)
            return len(path) > 0

    def report_in_path(self, name):
        path = self.get_path(name)
        if path:
            print("%s is in PATH: %s." % (name, path))
            return True
        else:
            print("%s is not in PATH." % name)
            return False

    def report_and_set_var(self, name):
        name = name.upper()
        val = os.environ.get("HDLMAKE_%s" % name)
        if val:
            print("Environmental variable HDLMAKE_%s is set: %s." % (name, val))
            self[name.lower()] = val
            return True
        else:
            print("Environmental variable HDLMAKE_%s is not set." % name)
            return False

if __name__ == "__main__":
    ec = EnvChecker({}, {})
    ec.check()
