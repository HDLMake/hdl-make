#!/usr/bin/python
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

import global_mod
import os
from util import path as path_mod


class DepRelation(object):
    # direction
    PROVIDE = 1
    USE = 2

    # rel_type
    ENTITY = 1
    PACKAGE = 2
    INCLUDE = 3

    def __init__(self, obj_name, direction, rel_type):
        assert direction in [DepRelation.PROVIDE, DepRelation.USE]
        assert rel_type in [DepRelation.ENTITY, DepRelation.PACKAGE, DepRelation.INCLUDE]
        self.direction = direction
        self.rel_type = rel_type
        self.obj_name = obj_name

    def satisfies(self, rel_b):
        if rel_b.direction == DepRelation.PROVIDE or self.direction == DepRelation.USE:
            return False
        if rel_b.rel_type == self.rel_type and rel_b.obj_name == self.obj_name:
            return True
        return False

    def library(self):
        if self.rel_type == DepRelation.PACKAGE:
            libdotpackage = self.obj_name
            try:
                lib, package = libdotpackage.split('.')
                return lib
            except ValueError:
                return None
        else:
            return None

    def __repr__(self):
        dstr = {self.USE: "Use", self.PROVIDE: "Provide"}
        ostr = {self.ENTITY: "entity/module", self.PACKAGE: "package", self.INCLUDE: "include/header"}
        return "%s %s '%s'" % (dstr[self.direction], ostr[self.rel_type], self.obj_name)

    def __hash__(self):
        return hash(self.__repr__())

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)


class File(object):
    def __init__(self, path, module=None):
        self.path = path
        if module is None:
            self.module = global_mod.top_module
        else:
            assert not isinstance(module, basestring)
            self.module = module

    @property
    def name(self):
        return os.path.basename(self.path)

    @property
    def purename(self):
        return os.path.splitext(self.name)[0]

    @property
    def dirname(self):
        return os.path.dirname(self.path)

    def rel_path(self, dir=None):
        if dir is None:
            dir = global_mod.current_path
        return path_mod.relpath(self.path, dir)

    def __str__(self):
        return self.path

    def __eq__(self, other):
        _NOTFOUND = object()
        v1, v2 = [getattr(obj, "path", _NOTFOUND) for obj in [self, other]]
        if v1 is _NOTFOUND or v2 is _NOTFOUND:
            return False
        elif v1 != v2:
            return False
        return True

    def __hash__(self):
        return hash(self.path)

    def __cmp__(self, other):
        if self.path < other.path:
            return -1
        if self.path == other.path:
            return 0
        if self.path > other.path:
            return 1

    def __ne__(self, other):
        return not self.__eq__(other)

    def isdir(self):
        return os.path.isdir(self.path)

    def show(self):
        print(self.path)

    def extension(self):
        tmp = self.path.rsplit('.')
        ext = tmp[len(tmp)-1]
        return ext


class DepFile(File):
    def __init__(self, file_path, module, include_paths=None):
        from module import Module
        assert isinstance(file_path, basestring)
        assert isinstance(module, Module)

        File.__init__(self, path=file_path, module=module)
        self.file_path = file_path
        self._rels = set()
        self.depends_on = set()  # set of files that the file depends on, items of type DepFile

        self.is_parsed = False
        if include_paths is None:
            include_paths = []
        else:
            pass
        self.file_path = file_path
        self.include_paths = include_paths

    def _parse_if_needed(self):
        from new_dep_solver import ParserFactory
        if not self.is_parsed:
            parser = ParserFactory().create(self)
            parser.parse(self)

    #use proxy template here
    def __get_rels(self):
        self._parse_if_needed()
        return self._rels

    def __set_rels(self, what):
        self._rels = what

    rels = property(__get_rels, __set_rels)

    def add_relation(self, rel):
        self._rels.add(rel)

    def satisfies(self, rel_b):
        assert isinstance(rel_b, DepRelation)
        self._parse_if_needed()
        return any(map(lambda x: x.satisfies(rel_b), self.rels))

    def show_relations(self):
        self._parse_if_needed()
        for r in self.rels:
            print(str(r))

    @property
    def filename(self):
        return os.path.basename(self.file_path)
