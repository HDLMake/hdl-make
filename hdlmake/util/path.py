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
import logging


def url_parse(url):
    """
    Check if link to a repo seems to be correct. Filter revision number and branch
    """
    """url_pat = re.compile("[ \t]*([^ \t]+?)[ \t]*(::)?([^ \t@]+)?(@[ \t]*(.+))?[ \t]*")
    url_match = re.match(url_pat, url)
    if url_match is None:
        print("Not a correct repo url: {0}. Skipping".format(url))
    url_clean = url_match.group(1)
    if url_match.group(3) is not None: #there is a branch
      branch = url_match.group(3)
    if url_match.group(5) is not None: #there is a revision given
      rev = url_match.group(5)"""
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
    words = url.split('//')
    try:
        words = words[1].split('/')
        return '/'.join(words[1:])
    except IndexError:
        return None


def pathsplit(p, rest=None):
    if rest is None:
        rest = []
    (h, t) = os.path.split(p)
    if len(h) < 1:
        return [t]+rest
    if len(t) < 1:
        return [h]+rest
    return pathsplit(h, [t]+rest)


def commonpath(l1, l2, common=None):
    if common is None:
        common = []
    if len(l1) < 1:
        return (common, l1, l2)
    if len(l2) < 1:
        return (common, l1, l2)
    if l1[0] != l2[0]:
        return (common, l1, l2)
    return commonpath(l1[1:], l2[1:], common+[l1[0]])


def is_rel_path(path):
    path = str(path)
    s = path[0]
    if s == '/' or s == '~':
        return False
    return True


def is_abs_path(path):
    path = str(path)
    s = path[0]
    if s == '/':
        return True
    return False


def relpath(p1, p2=None):
    if p2 is None:
        p2 = os.getcwd()
    if p1 == p2:
        return '.'
    p1, p2 = p2, p1
    if p1[-1] == '/':
        p1 = p1[:-1]
    if p2[-1] == '/':
        p2 = p2[:-1]

    (_, l1, l2) = commonpath(pathsplit(p1), pathsplit(p2))
    p = []
    if len(l1) > 0:
        p = ['../' * len(l1)]
    p = p + l2
    return os.path.join(*p)


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
