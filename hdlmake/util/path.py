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


def url_parse(url):
    """
    Check if link to a Git repo seems to be correct. Filter revision
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


def svn_parse(url):
    """
    Check if link to a SVN repo seems to be correct. Filter revision
    number
    """
    url_clean, rev = None, None
    if "@" in url:
        url_clean, rev = url.split("@")
    else:
        url_clean = url

    return (url_clean, rev)


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
    return os.path.relpath(os.path.abspath(
        os.path.join(base, path)))


def flatten_list(sth):
    """Convert the argument in a list, being an empty list if none"""
    if sth is not None:
        if not isinstance(sth, (list, tuple)):
            sth = [sth]
    else:
        sth = []
    return sth
