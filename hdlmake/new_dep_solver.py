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


from __future__ import print_function
import logging
import tools


class DepParser(object):
    def __init__(self, dep_file):
        self.dep_file = dep_file

    def parse():
        raise


class ParserFactory(object):
    def create(self, dep_file):
        import re
        from vlog_parser import VerilogParser
        from vhdl_parser import VHDLParser

        extension = re.match(re.compile(".+\.(\w+)$"), dep_file.file_path)
        if not extension:
            raise ValueError("Unecognized file format : %s" % dep_file.file_path)
        extension = extension.group(1).lower()
        if extension in ["vhd", "vhdl"]:
            return VHDLParser(dep_file)
        elif extension in ["v", "sv"]:
            vp = VerilogParser(dep_file)
            for d in dep_file.include_paths:
                vp.add_search_path(d)
            return vp

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
    from dep_file import DepFile, DepRelation
    assert isinstance(fileset, SourceFileSet)

    fset = fileset.filter(DepFile)

    # for fle in fset:
    #     print(fle.path)
    #     for rel in fle.rels:
    #         print('\t' + str(rel))

    for investigated_file in fset:
        for rel in investigated_file.rels:
            if rel.direction is DepRelation.PROVIDE:  # PROVIDE relations dont have to be satisfied
                continue
            if rel.rel_type is DepRelation.INCLUDE:  # INCLUDE are already solved by preprocessor
                continue
            if rel.library() in tools.get_standard_libraries():  # dont care about standard libs
                continue

            satisfied_by = set()
            for dep_file in fset:
                if dep_file is investigated_file:
                    continue
                if dep_file.satisfies(rel):
                    investigated_file.depends_on.add(dep_file)
                    satisfied_by.add(dep_file)
            if len(satisfied_by) > 1:
                logging.warning("Relation %s satisfied by multpiple (%d) files: %s",
                                str(rel),
                                len(satisfied_by),
                                '\n'.join([file.path for file in list(satisfied_by)]))
            elif len(satisfied_by) == 0:
                logging.warning("Relation %s not satisfied by any source file", str(rel))
    logging.info("Dependencies solved")


def make_dependency_sorted_list(fileset, purge_unused=True):
    pass
    # return list of files sorted in dependency order

if __name__ == "__main__":
    from dep_file import (DepFile)
    logging.basicConfig(format="%(levelname)s %(funcName)s() %(filename)s:%(lineno)d: %(message)s", level=logging.DEBUG)
    df = DepFile("/home/pawel/cern/hdl-make/tests/lr_test/wr-cores/modules/wrc_lm32/lm32_shifter.v", [])
    df.show_relations()

    print("-----------------------\n"
          "---------- VHDL -------\n"
          "-----------------------\n")
    df1 = DepFile("/home/pawel/cern/hdl-make/examples/fine_delay/hdl/testbench/top/wr-cores/testbench/top_level/gn4124_bfm/mem_model.vhd")
    df1.show_relations()
