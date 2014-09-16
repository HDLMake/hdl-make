#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013, 2014 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Multi-tool support by Javier D. Garcia-Lasheras (javier@garcialasheras.com)
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

import global_mod
import importlib

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


def _green(text):
    return colored(text, 'green')


def _red(text):
    return colored(text, 'red')


class Env(dict):

    #def __init__(self, options, top_module=None):
    def __init__(self, options):
        dict.__init__(self)
        self.options = options
        #self.top_module = top_module


    def check_env(self, verbose=True):
        print.set_verbose(verbose)
        # Check and determine general environment
        self._check_general()
        tool_object = global_mod.tool_module.ToolControls()      
        self._check_tool(tool_object)
        self._check_remote_tool(tool_object)


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


    def _check_general(self):
        self["architecture"] = 64 if _64bit_architecture else 32
        self["platform"] = sys.platform
        print("Architecture: %s" % self["architecture"])
        print("Platform: %s" % self["platform"])

        # general
        print("### General variabless ###")
        self._report_and_set_hdlmake_var("coredir")
        if self["coredir"] is not None:
            print("All modules will be fetched to %s" % path.rel2abs(self["coredir"]))
        else:
            print("'fetchto' variables in the manifests will be respected when fetching.")


    def _check_tool(self, info_class):
        
        tool_info = info_class.get_keys()
        if sys.platform == 'cygwin':
            bin_name = tool_info['windows_bin']
        else:
            bin_name = tool_info['linux_bin']

        path_key = tool_info['id'] + '_path'
        version_key = tool_info['id'] + '_version'
        name = tool_info['name']

        print("\n### " + name + " tool environment information ###")
        self._report_and_set_hdlmake_var(path_key)
        if self[path_key] is not None:
            if self._is_in_path(bin_name, self[path_key]):
                print(name + " " + _green("found") + " under HDLMAKE_" + path_key.upper() + ": %s" % self[path_key])
            else:
                print(name + " " + _red("NOT found") + " under HDLMAKE_" + path_key.upper() + ": %s" % self[path_key])
        else:
            if self._check_in_system_path(bin_name):
                self[path_key] = self._get_path(bin_name)
                print(name + " " + _green("found") + " in system path: %s" % self[path_key])
            else:
                print(name + " " + _red("cannnot") + " be found.")
        if self[path_key] is not None:
            self[version_key] = info_class.detect_version(self[path_key])
            print("Detected " + name +" version %s" % self[version_key])


    def _check_remote_tool(self, info_class):

        tool_info = info_class.get_keys()
        remote_path_key = 'rsynth_' + tool_info['id'] + '_path'
        remote_version_key = 'rsynth_' + tool_info['id'] + '_version'
        name = tool_info['name']
        
        print("\n### Remote tool " + name + " environment information ###")
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

        self._report_and_set_hdlmake_var(remote_path_key)
        if can_connect and self[remote_path_key] is not None:
            ssh_cmd = 'ssh -o BatchMode=yes -o ConnectTimeout=5 %s@%s test -e %s 2>&1'
            ssh_cmd = ssh_cmd % (self["rsynth_user"], self["rsynth_server"], self[remote_path_key])
            ssh_out = Popen(ssh_cmd, shell=True, stdin=PIPE, stdout=PIPE, close_fds=True)
            ssh_response = ssh_out.returncode
            if ssh_response == 0:
                print("%s found on remote machine under %s." % (name, self[remote_path_key]))
            else:
                print("Can't find %s on remote machine under %s." % (name, self[remote_path_key]))
        self._report_and_set_hdlmake_var("rsynth_use_screen")
        if self["rsynth_use_screen"]:
            print("Remote execution will use screen.")
        else:
            print("To use screen, set it to '1'.")


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


    ## TODO: TRANSFORM THIS INTO A GENERAL VERSION FORCE/CHECK MECHANISM OR SUPRESS???
    #def check_env_wrt_manifest(self, verbose=False):
    #    # determine ISE version
    #    if self.top_module:
    #        if self.top_module.syn_ise_version is not None:
    #            ise_version = self.top_module.syn_ise_version
    #            print("ise_version set in the manifest: %s" % ise_version)
    #            self["ise_version"] = ise_version
    #        elif self["ise_version"] is not None:
    #            iv = self["ise_version"]
    #            print("syn_ise_version not set in the manifest,"
    #                  " guessed ISE version: %s.%s." % (iv[0], iv[1]))



if __name__ == "__main__":
    ec = Env({}, {})
    ec.check()
