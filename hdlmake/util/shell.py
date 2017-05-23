#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017 CERN
# Author: Javier Garcia (jgarcia@gl-research.com)
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

"""This module provides stuff for cross shell and O.S. support"""

from __future__ import print_function
from __future__ import absolute_import
import os
import sys
import platform
import logging
from subprocess import PIPE, Popen, CalledProcessError


def run(command):
    """Execute a command in the shell and print the output lines as a list"""
    try:
        command_out = Popen(command,
            stdout=PIPE,
            stdin=PIPE,
            stderr=PIPE,
            close_fds=not check_windows(),
            shell=True)
        lines = command_out.stdout.readlines()
        if len(lines) == 0:
            return None
        return lines[0].strip()
    except CalledProcessError as process_error:
        logging.error("Cannot clean the module: %s",
            process_error.output)
        quit()


def tclpath(path):
    """Convert a O.S. specific path into a TCL friendly one"""
    return path.replace(slash_char(), "/")


def check_windows():
    """Check if we are operating on a Windows filesystem"""
    if platform.system() == 'Windows' or sys.platform == 'cygwin':
        return True
    else:
        return False


def del_command():
    """Get a string with the O.S. specific delete command"""
    if check_windows():
        return "del /s /q /f"
    else:
        return "rm -rf"


def rmdir_command():
    """Get a string with the O.S. specific remove directory command"""
    if check_windows():
        return "rmdir /s /q"
    else:
        return "rm -rf"


def copy_command():
    """Get a string with the O.S. specific copy command"""
    if check_windows():
        return "copy"
    else:
        return "cp"


def mkdir_command():
    """Get a string with the O.S. specific mkdir command"""
    if check_windows():
        return "mkdir"
    else:
        return "mkdir -p"


def touch_command():
    """Get a string with the O.S. specific mkdir command"""
    if check_windows():
        return "type nul >>"
    else:
        return "touch"


def which(filename):
    """Implement the which function and return the paths as a string list"""
    locations = os.environ.get("PATH").split(os.pathsep)
    candidates = []
    for location in locations:
        candidate = os.path.join(location, filename)
        if os.path.isfile(candidate.split()[0]):
            candidates.append(candidate)
    return candidates


def which_cmd():
    """Get a string with the O.S. specific which command"""
    if check_windows():
        return "where"
    else:
        return "which"


def slash_char():
    """Get a string with the O.S. specific path separator"""
    if check_windows():
        return "\\"
    else:
        return "/"


def architecture():
    """Get a string with the O.S. bus width"""
    import struct
    return 64 if struct.calcsize('P') * 8 == 64 else 32
