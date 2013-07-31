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
    def _get_path(arch, major, minor):
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


class Env(dict):
    def __init__(self, options, top_module):
        dict.__init__(self)
        self.options = options
        self.top_module = top_module

    def check(self, verbose=False):
        print.set_verbose(verbose)
        platform = sys.platform
        print("Platform: %s" % platform)

        # general
        print("### General variabless ###")
        self._report_and_set_hdlmake_var("coredir")
        if self["coredir"] is not None:
            print("All modules will be fetched to %s" % path.rel2abs(self["coredir"]))

        # determine path for Quartus
        print("\n### Quartus synthesis ###")
        self._report_and_set_hdlmake_var("quartus_path")
        if self["quartus_path"] is not None:
            if self._check_in_path("quartus", self["quartus_path"]):
                print("quartus found under HDLMAKE_QUARTUS_PATH: %s" % self["quartus_path"])
            else:
                print("quartus NOT found under HDLMAKE_quartus_PATH: %s" % self["quartus_path"])
        else:
            if self._check_in_system_path("quartus"):
                self["quartus_path"] = self._get_path("quartus")
                print("quartus found in system path: %s" % self["quartus_path"])
            else:
                print("quartus can't be found.")

        # determine path for ise
        print("\n### ISE synthesis ###")
        xilinx = os.environ.get("XILINX")
        if xilinx:
            print("Environmental variable %s is set: %s." % ("XILINX", xilinx))
            self["xilinx"] = xilinx
        else:
            print("Environmental variable XILINX is not set.")

        self._report_and_set_hdlmake_var("ise_path")
        if self["xilinx"] is not None:
            if self["ise_path"] is not None:
                print("HDLMAKE_ISE_PATH and XILINX can't be set at a time\n"
                      "Ignoring HDLMAKE_ISE_PATH")
            else:
                pass
            self["ise_path"] = os.path.join(self["xilinx"], "ISE/bin/lin")
        if self["ise_path"] is not None:
            if self._check_in_path("ise", self["ise_path"]):
                print("ISE found in HDLMAKE_ISE_PATH: %s." % self["ise_path"])
            else:
                print("ISE not found in HDLMAKE_ISE_PATH: %s." % self["ise_path"])
        else:
            if self._check_in_path("ise"):
                print("ISE found in PATH: %s." % self._get_path("ise"))
            else:
                print("ISE not found in PATH.")

        # determine ISE version
        if self.top_module:
            if self.top_module.syn_ise_version is not None:
                ise_version = tuple(self.top_module.syn_ise_version)
                print("ise_version set in the manifest: %s.%s" % (ise_version[0], ise_version[1]))
                self["ise_version"] = ise_version
            else:
                ise_version = None

            if "ise_version" not in self:
                ise_version = self._guess_ise_version(xilinx, '')
                if ise_version:
                    print("syn_ise_version not set in the manifest,"
                          " guessed ISE version: %s.%s." % (ise_version[0], ise_version[1]))
                self["ise_version"] = ise_version

            #######

        # determine modelsim path
        print("\n### Modelsim simulation ###")
        self._report_and_set_hdlmake_var("modelsim_path")
        if self["modelsim_path"] is not None:
            if self._check_in_path("vsim", self["modelsim_path"]):
                print("vsim found in HDLMAKE_MODELSIM_PATH: %s." % self["modelsim_path"])
            else:
                print("vsim NOT found in HDLMAKE_MODELSIM_PATH: %s." % self["modelsim_path"])
        else:
            if self._check_in_system_path("vsim"):
                self["modelsim_path"] = self._get_path("modelsim_path")
                print("vsim found in system PATH: %s." % self["modelsim_path"])
            else:
                print("vsim can't be found.")

        # determine iverilog path
        print("\n### Iverilog simulation ###")
        self._report_and_set_hdlmake_var("iverilog_path")
        if self["iverilog_path"] is not None: 
            if self._check_in_path("iverilog", self["iverilog_path"]):
                print("iverilog found under HDLMAKE_IVERILOG_PATH: %s" % self["iverilog_path"])
            else:
                print("iverilog NOT found under HDLMAKE_IVERILOG_PATH: %s" % self["iverilog_path"])
        else:
            if self._check_in_system_path("iverilog"):
                self["iverilog_path"] = self._get_path("iverilog")
                print("iverilog found in system path: %s" % self["iverilog_path"])
            else:
                print("iverlog can't be found.")

        # determine isim path
        print("\n### ISim simulation ###")
        self._report_and_set_hdlmake_var("isim_path")

        if self["isim_path"] is not None:
            if self._check_in_path("isim", self["isim_path"]):
                print("isim found under HDLMAKE_ISIM_PATH: %s" % self["isim_path"])
            else:
                print("isim NOT found under HDLMAKE_ISIM_PATH: %s" % self["isim_path"])
        else:
            if self["xilinx"] is not None:
                #### TODO:rely on the XILINX var
                pass
            else:
                if self._check_in_system_path("isim"):
                    self["isim_path"] = self._get_path("isim")
                    print("isim found in system path: %s" % self["isim_path"])
                else:
                    print("iverlog can't be found.")

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
        rsynth_screen = self._get("rsynth_use_screen")
        if rsynth_screen:
            if rsynth_screen == '1':
                print("Environmental variable HDLMAKE_RSYNTH_USE_SCREEN is set to 1. Remote synthesis will use screen.")
            else:
                print("Environmental variable HDLMAKE_RSYNTH_USE_SCREEN is set to %s.To use screen, set it to '1'." % rsynth_screen)
        else:
            print("Environmental variable HDLMAKE_RSYNTH_USE_SCREEN is unset. Set it to '1' to use screen in remote synthesis")

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
            ise_version = (match.group('major'), match.group('minor'))
        else:  # If it is not the case call the "xst -h" to get version
            xst_output = Popen('xst -h', shell=True, stdin=PIPE,
                               stdout=PIPE, close_fds=True)
            xst_output = xst_output.stdout.readlines()[0]
            xst_output = xst_output.strip()
            version_pattern = re.compile('Release\s(?P<major>\d|\d\d)[^\d](?P<minor>\d|\d\d)\s.*')
            match = re.match(version_pattern, xst_output)
            if match:
                ise_version = (match.group('major'), match.group('minor'))
            else:
                logging.error("xst output is not in expected format: %s\n" % xst_output +
                              "Can't determine ISE version")
                return None

        return ise_version

    def _get(self, name):
        assert not name.startswith("HDLMAKE_")
        assert isinstance(name, basestring)
        name = name.upper()

        return os.environ.get("HDLMAKE_%s" % name)

    def _get_path(self, name):
        return os.popen("which %s" % name).read().strip()

    def _check_in_path(self, name, path=None):
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
            print("Environmental variable HDLMAKE_%s is set: %s." % (name, val))
            self[name.lower()] = val
            return True
        else:
            print("Environmental variable HDLMAKE_%s is not set." % name)
            self[name.lower()] = None
            return False

if __name__ == "__main__":
    ec = Env({}, {})
    ec.check()
