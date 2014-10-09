#!/usr/bin/python
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
import logging
from dep_file import DepFile

from srcfile import VHDLFile, VerilogFile, SVFile

import global_mod


class DepParser(object):
    def __init__(self, dep_file):
        self.dep_file = dep_file

    def parse(self, dep_file):
        raise


class ParserFactory(object):
    def create(self, dep_file):
        import re
        from vlog_parser import VerilogParser
        from vhdl_parser import VHDLParser
        
        if isinstance(dep_file, VHDLFile) :
            return VHDLParser(dep_file)
        elif isinstance(dep_file, VerilogFile) or isinstance(dep_file,  SVFile) :
            vp = VerilogParser(dep_file)
            for d in dep_file.include_paths:
                vp.add_search_path(d)
            return vp
        else :
            raise ValueError("Unecognized file format : %s" % dep_file.file_path)

# class DepSolver(object):
#     def solve(self, vhdl_files):
#         for f in vhdl_files:
#             logging.debug("solving deps for " + f.path)
#             if f.dep_requires:
#                 for req in f.dep_requires:
#                     pf = self._find_provider_file(req=req, vhdl_file=f, fset=vhdl_files)
#                     assert isinstance(pf, SourceFile)
#                     if not pf:
#                         logging.error("Missing dependency in file "+str(f)+": " + req[0]+'.'+req[1])
#                     else:
#                         logging.debug("%s depends on %s" % (f.path, pf.path))
#                         if pf.path != f.path:
#                             f.dep_depends_on.append(pf)
#             #get rid of duplicates by making a set from the list and vice versa
#             f.dep_depends_on = list(set(f.dep_depends_on))
#             f.dep_resolved = True


def solve(fileset):
    from srcfile import SourceFileSet
    from dep_file import DepRelation
    assert isinstance(fileset, SourceFileSet)
    fset = fileset.filter(DepFile)

    # for fle in fset:
    #     print(fle.path)
    #     for rel in fle.rels:
    #         print('\t' + str(rel))
    not_satisfied = 0
    for investigated_file in fset:
        logging.debug("Dependency solver investigates %s (%d relations)" % (investigated_file, len(investigated_file.rels)))
        for rel in investigated_file.rels:
            if rel.direction is DepRelation.PROVIDE:  # PROVIDE relations dont have to be satisfied
                continue
            if rel.rel_type is DepRelation.INCLUDE:  # INCLUDE are already solved by preprocessor
                continue
            if rel.library() in global_mod.tool_module.ToolControls().get_standard_libraries():  # dont care about standard libs
                continue
            satisfied_by = set()
            for dep_file in fset:
               # if dep_file is investigated_file:
               #     continue
                if dep_file.satisfies(rel):
                    investigated_file.depends_on.add(dep_file)
                    satisfied_by.add(dep_file)
            if len(satisfied_by) > 1:
                logging.warning("Relation %s satisfied by multpiple (%d) files: %s",
                                str(rel),
                                len(satisfied_by),
                                '\n'.join([file.path for file in list(satisfied_by)]))
            elif len(satisfied_by) == 0:
                logging.warning("Relation %s in %s not satisfied by any source file" % (str(rel), investigated_file.name))
                not_satisfied += 1
    if not_satisfied != 0:
        logging.info("Dependencies solved, but %d relations were not satisfied.\n"
                     "It doesn't necessarily mean that there is some file missing, as it might be defined\n"
                     "internally in the compiler." % not_satisfied)
    else:
        logging.info("Dependencies solved")


def make_dependency_sorted_list(fileset, purge_unused=True):
    # CYCLE_THRESHOLD = 30
    # ret = list(fileset)
    # cur_idx = 0
    # other_file_idx = cur_idx + 1
    # swapped = 0
    # while True:
    #     if swapped >= CYCLE_THRESHOLD:
    #         cur_idx += 1
    #     if cur_idx >= len(ret):
    #         break
    #     if other_file_idx >= len(ret):
    #         cur_idx += 1
    #         other_file_idx = cur_idx + 1
    #         continue
    #     dep_file = ret[cur_idx]
    #     other_file = ret[other_file_idx]
    #     if other_file in dep_file.depends_on:
    #         ret[cur_idx], ret[other_file_idx] = ret[other_file_idx], ret[cur_idx]
    #         other_file_idx = cur_idx + 1
    #         swapped += 1
    #     else:
    #         other_file_idx += 1
    # return ret
    def compare_dep_files(f1, f2):
        if f2 in f1.depends_on:
            return 1
        if f1 in f2.depends_on:
            return -1
        return 0

    filelist = list(fileset)
    dependable = [file for file in filelist if isinstance(file, DepFile)]
    non_depednable = [file for file in filelist if not isinstance(file, DepFile)]
    ret = non_depednable
    dependable_sorted = sorted(dependable, cmp=compare_dep_files)
    ret.extend(dependable_sorted)
    return ret
