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

"""This module provides a set of functions that are commonly used in HDLMake"""

from __future__ import print_function
from __future__ import absolute_import
import os
import sys
import logging
import platform


def url_parse(url):
    """
    Check if link to a repo seems to be correct. Filter revision
    number and branch
    """
    url_clean, branch, rev = None, None, None
    if "@@" in url:
        url_clean, rev = url.split("@@")
    elif "::" in url:
        url_clean, branch = url.split("::")
    else:
        url_clean = url

    return (url_clean, branch, rev)


def url_basename(url):
    """
    Get basename from an url
    """
    if url.endswith(".git"):
        parts = url[:-4].split("/")
    elif url[-1] == '/':
        parts = url[:-1].split("/")
    else:
        parts = url.split("/")
    ret = parts[-1]
    return ret


def svn_basename(url):
    """
    Get basename from an SVN url
    """
    words = url.split('//')
    try:
        words = words[1].split('/')
        return '/'.join(words[1:])
    except IndexError:
        return None


def pathsplit(path, rest=None):
    """
    Split the provided path and return as a tuple
    """
    if rest is None:
        rest = []
    (head, tail) = os.path.split(path)
    if len(head) < 1:
        return [tail] + rest
    if len(tail) < 1:
        return [head] + rest
    return pathsplit(head, [tail] + rest)


def commonpath(path1, path2, common=None):
    """
    Return the common path for the provided paths
    """
    if common is None:
        common = []
    if len(path1) < 1:
        return (common, path1, path2)
    if len(path2) < 1:
        return (common, path1, path2)
    if path1[0] != path2[0]:
        return (common, path1, path2)
    return commonpath(path1[1:], path2[1:], common + [path1[0]])


def is_rel_path(path):
    """Check if the given path is relative"""
    return not os.path.isabs(path)


def is_abs_path(path):
    """Check if the given path is absolute"""
    return os.path.isabs(path)


def relpath(path1, path2=None):
    """Return the relative path of one path with respect to the other"""
    if path2 is None:
        path2 = os.getcwd()
    if path1 == path2:
        return '.'
    return os.path.relpath(path1, path2)


def rel2abs(path, base=None):
    """
    converts a relative path to an absolute path.

    @param path the path to convert - if already absolute, is returned
    without conversion.
    @param base - optional. Defaults to the current directory.
    The base is intelligently concatenated to the given relative path.
    @return the relative path of path from base
    """
    if base is None:
        base = os.getcwd()
    if os.path.isabs(path):
        return path
    retval = os.path.join(base, path)
    return os.path.abspath(retval)


def compose(path, base=None):
    """Get the relative path composition of the provided path"""
    if base is None:
        base = os.getcwd()
    return os.path.relpath(os.path.abspath(os.path.join(base, path)))


def search_for_manifest(search_path):
    """
    Look for manifest in the given folder
    """
    logging.debug("Looking for manifest in " + search_path)
    for filename in os.listdir(search_path):
        if filename == "manifest.py" and not os.path.isdir(filename):
            return os.path.abspath(os.path.join(search_path, filename))
    # no manifest file found
    return None


def flatten_list(sth):
    """Convert the argument in a list, being an empty list if none"""
    if sth is not None:
        if not isinstance(sth, (list, tuple)):
            sth = [sth]
    else:
        sth = []
    return sth


def check_windows():
    """Check if we are operating on a Windows filesystem"""
    if platform.system() == 'Windows' or sys.platform == 'cygwin':
        return True
    else:
        return False


def del_command():
    """Get a string with the O.S. specific delete command"""
    if check_windows():
        return "rm -rf"
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
    return 64 if sys.maxsize > 2 ** 32 else 32
