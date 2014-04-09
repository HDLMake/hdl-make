#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
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
#

from __future__ import print_function
import os
import sys
from subprocess import Popen, PIPE
import re
import logging
import os.path
from util import path
from util.termcolor import colored
from tools.ise import detect_ise_version
from tools.modelsim import detect_modelsim_version
from tools.quartus import detect_quartus_version
from tools.isim import detect_isim_version
from tools.iverilog import detect_iverilog_version

_plain_print = print


class _PrintClass(object):
    def __init__(self):
        self.verbose = None

    def set_verbose(self, verbose):
        self.verbose = verbose

    def __call__(self, *args, **kwargs):
        if self.verbose:
            _plain_print(*args, **kwargs)

print = _PrintClass()
_64bit_architecture = sys.maxsize > 2**32

class _IsePath(object):
    _ise_path_32 = {
        10: {0: "/opt/Xilinx/10.0/ISE/bin/lin",
             1: "/opt/Xilinx/10.1/ISE/bin/lin"},
        12: {1: "/opt/Xilinx/12.1/ISE_DS/ISE/bin/lin",
             2: "/opt/Xilinx/12.2/ISE_DS/ISE/bin/lin",
             4: "/opt/Xilinx/12.4/ISE_DS/ISE/bin/lin"},
        13: {1: "/opt/Xilinx/13.1/ISE_DS/ISE/bin/lin"}
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
    def _get_path(arch, major, minor):
        if arch == 32:
            dct = _IsePath._ise_path_32
        else:
            dct = _IsePath._ise_path_64

        try:
            minor_dct = dct[major]
            try:
                ise_path = minor_dct[minor]
                return ise_path
            except KeyError:
                #get latest for the chosen major version
                minor_keys = sorted(minor_dct.keys())
                max_minor_key = minor_keys[-1]
                ise_path = minor_dct[max_minor_key]

        except KeyError:
            #get path for the latest version from the dict
            major_keys = sorted(dct.keys())
            max_major_key = major_keys[-1]
            minor_dct = dct[max_major_key]
            minor_keys = sorted(minor_dct.keys())
            max_minor_key = minor_keys[-1]
            ise_path = minor_dct[max_minor_key]
            return ise_path


def _green(text):
    return colored(text, 'green')


def _red(text):
    return colored(text, 'red')


class Env(dict):
    def __init__(self, options, top_module=None):
        dict.__init__(self)
        self.options = options
        self.top_module = top_module

    def check_env_wrt_manifest(self, verbose=False):
        # determine ISE version
        if self.top_module:
            if self.top_module.syn_ise_version is not None:
                ise_version = self.top_module.syn_ise_version
                print("ise_version set in the manifest: %s" % ise_version)
                self["ise_version"] = ise_version
            elif self["ise_version"] is not None:
                iv = self["ise_version"]
                print("syn_ise_version not set in the manifest,"
                      " guessed ISE version: %s.%s." % (iv[0], iv[1]))

    def check_env(self, verbose=False):
        print.set_verbose(verbose)
        self["architecture"] = 64 if _64bit_architecture else 32
        platform = sys.platform
        print("Platform: %s" % platform)

        # general
        print("### General variabless ###")
        self._report_and_set_hdlmake_var("coredir")
        if self["coredir"] is not None:
            print("All modules will be fetched to %s" % path.rel2abs(self["coredir"]))
        else:
            print("'fetchto' variables in the manifests will be respected when fetching.")

        # determine path for Quartus
        print("\n### Quartus synthesis ###")
        self._report_and_set_hdlmake_var("quartus_path")
        if self["quartus_path"] is not None:
            if self._is_in_path("quartus", self["quartus_path"]):
                print(("Quartus " + _green("found") + " under HDLMAKE_QUARTUS_PATH: %s") % self["quartus_path"])
            else:
                print(("Quartus " + _red("NOT found") + " under HDLMAKE_quartus_PATH: %s") % self["quartus_path"])
        else:
            if self._check_in_system_path("quartus"):
                self["quartus_path"] = self._get_path("quartus")
                print(("Quartus " + _green("found") + " in PATH: %s") % self["quartus_path"])
            else:
                print("Quartus " + _red("not found"))

        # determine path for ise
        print("\n### ISE synthesis ###")
        xilinx = os.environ.get("XILINX")
        if xilinx:
            print(("Environmental variable %s " + _green("is set:") + ' "%s".') % ("XILINX", xilinx))
            self["xilinx"] = xilinx
        else:
            self["xilinx"] = None
            print("Environmental variable XILINX " + _red("is not set."))

        self._report_and_set_hdlmake_var("ise_path")
        if self["xilinx"] is not None:
            if self["ise_path"] is not None:
                print("HDLMAKE_ISE_PATH and XILINX can't be set at a time\n"
                      "Ignoring HDLMAKE_ISE_PATH")
            else:
                pass
            self["ise_path"] = os.path.join(self["xilinx"], 'bin', 'lin64' if _64bit_architecture else 'lin')
            print("HDLMAKE_ISE_PATH infered from XILINX variable: %s" % self["ise_path"])

        self["ise_version"] = None
        if self["ise_path"] is not None:
            if self._is_in_path("ise", self["ise_path"]):
                print(("ISE " + _green("found") + " in HDLMAKE_ISE_PATH: %s.") % self["ise_path"])
                self["ise_version"] = detect_ise_version(self["ise_path"])
            else:
                print(("ISE " + _red("not found") + " in HDLMAKE_ISE_PATH: %s.") % self["ise_path"])
        else:
            if self._is_in_path("ise"):
                print(("ISE " + _green("found") + " in PATH: %s.") % self._get_path("ise"))
                self["ise_version"] = detect_ise_version(self._get_path("ise"))
            else:
                print("ISE " + _red("not found"))
        if self["ise_version"] is not None:
            print("Detected ISE version %s" % self["ise_version"])

        # determine modelsim path
        print("\n### Modelsim simulation ###")
        self._report_and_set_hdlmake_var("modelsim_path")
        if self["modelsim_path"] is not None:
            if self._is_in_path("vsim", self["modelsim_path"]):
                print("vsim " + _green("found") + " in HDLMAKE_MODELSIM_PATH: %s." % self["modelsim_path"])
            else:
                print("vsim " + _red("not found") + " in HDLMAKE_MODELSIM_PATH: %s." % self["modelsim_path"])
        else:
            if self._check_in_system_path("vsim"):
                self["modelsim_path"] = self._get_path("vsim")
                print("vsim " + _green("found") + " in system PATH: %s." % self["modelsim_path"])
            else:
                print("vsim " + _red("cannot") + " be found.")
        if self["modelsim_path"] is not None:
            self["modelsim_version"] = detect_modelsim_version(self["modelsim_path"])
            print("Detected Modelsim version %s " % self["modelsim_version"])


        # determine iverilog path
        print("\n### Iverilog simulation ###")
        self._report_and_set_hdlmake_var("iverilog_path")
        if self["iverilog_path"] is not None:
            if self._is_in_path("iverilog", self["iverilog_path"]):
                print("iverilog " + _green("found") + " under HDLMAKE_IVERILOG_PATH: %s" % self["iverilog_path"])
            else:
                print("iverilog " + _red("NOT found") + " under HDLMAKE_IVERILOG_PATH: %s" % self["iverilog_path"])

        else:
            if self._check_in_system_path("iverilog"):
                self["iverilog_path"] = self._get_path("iverilog")
                print("iverilog " + _green("found") + " in system path: %s" % self["iverilog_path"])
            else:
                print("iverlog " + _red("cannnot") + " be found.")
        if self["iverilog_path"] is not None:
            self["iverilog_version"] = detect_iverilog_version(self["iverilog_path"])
            print("Detected iverilog version %s" % self["iverilog_version"])

        # determine isim path
        print("\n### ISim simulation ###")
        self._report_and_set_hdlmake_var("isim_path")

        if self["isim_path"] is not None:
            if self._is_in_path("isim", self["isim_path"]):
                print("isim " + _green("found") + " under HDLMAKE_ISIM_PATH: %s" % self["isim_path"])
            else:
                print("isim " + _red("NOT found") + " under HDLMAKE_ISIM_PATH: %s" % self["isim_path"])
        elif self["ise_path"] is not None:
            self["isim_path"] = self["ise_path"]
            print("Infered HDLMAKE_ISIM_PATH from ISE path: %s" % self["isim_path"])
        else:
            if self["xilinx"] is not None:
                self["isim_path"] = os.path.join(self["xilinx"], 'bin', 'lin64' if _64bit_architecture else 'lin')
                print("HDLMAKE_ISE_PATH infered from XILINX variable: %s" % self["ise_path"])
            else:
                if self._check_in_system_path("isim"):
                    self["isim_path"] = self._get_path("isim")
                    print("isim " + _green("found") + " in system path: %s" % self["isim_path"])
                else:
                    print("isim " + _red("cannnot") + " be found.")
        if self["isim_path"] is not None:
            self["isim_version"] = detect_isim_version(self["isim_path"])
            print("Detected isim version %s" % self["isim_version"])

        # remote synthesis with ise
        print("\n### Remote synthesis with ISE ###")
        self._report_and_set_hdlmake_var("rsynth_user")
        self._report_and_set_hdlmake_var("rsynth_server")
        can_connect = False
        if self["rsynth_user"] is not None and self["rsynth_server"] is not None:
            ssh_cmd = 'ssh -o BatchMode=yes -o ConnectTimeout=5 %s@%s echo ok 2>&1'
            ssh_cmd = ssh_cmd % (self["rsynth_user"], self["rsynth_server"])
            ssh_out = Popen(ssh_cmd, shell=True, stdin=PIPE, stdout=PIPE, close_fds=True)
            ssh_response = ssh_out.stdout.readlines()[0].strip()
            if ssh_response == "ok":
                print("Can connect to the remote machine: %s@%s." % (self["rsynth_user"], self["rsynth_server"]))
                can_connect = True
            else:
                print("Can't make a passwordless connection to the remote machine: %s@%s" % (self["rsynth_user"], self["rsynth_server"]))
                can_connect = False

        self._report_and_set_hdlmake_var("rsynth_ise_path")
        if can_connect and self["rsynth_ise_path"] is not None:
            ssh_cmd = 'ssh -o BatchMode=yes -o ConnectTimeout=5 %s@%s test -e %s 2>&1'
            ssh_cmd = ssh_cmd % (self["rsynth_user"], self["rsynth_server"], self["rsynth_ise_path"])
            ssh_out = Popen(ssh_cmd, shell=True, stdin=PIPE, stdout=PIPE, close_fds=True)
            ssh_response = ssh_out.returncode
            if ssh_response == 0:
                print("ISE found on remote machine under %s." % self["rsynth_ise_path"])
            else:
                print("Can't find ISE on remote machine under %s." % self["rsynth_ise_path"])
        self._report_and_set_hdlmake_var("rsynth_use_screen")
        if self["rsynth_use_screen"]:
            print("Remote synthesis will use screen.")
        else:
            print("To use screen, set it to '1'.")

    def _get(self, name):
        assert not name.startswith("HDLMAKE_")
        assert isinstance(name, basestring)
        name = name.upper()

        return os.environ.get("HDLMAKE_%s" % name)

    def _get_path(self, name):
        location = os.popen("which %s" % name).read().strip()
        return os.path.dirname(location)

    def _is_in_path(self, name, path=None):
        if path is not None:
            return os.path.exists(os.path.join(path, name))
        else:
            assert isinstance(name, basestring)
            path = self._get_path(name)
            return len(path) > 0

    def _check_in_system_path(self, name):
        path = self._get_path(name)
        if path:
            return True
        else:
            return False

    def _report_and_set_hdlmake_var(self, name):
        name = name.upper()
        val = self._get(name)
        if val:
            print(("Environmental variable HDLMAKE_%s " + _green("is set:") + ' "%s".') % (name, val))
            self[name.lower()] = val
            return True
        else:
            print(("Environmental variable HDLMAKE_%s " + _red("is not set.")) % name)
            self[name.lower()] = None
            return False

if __name__ == "__main__":
    ec = Env({}, {})
    ec.check()
