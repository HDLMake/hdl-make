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

from .dep_file import DepFile
from .srcfile import VHDLFile, VerilogFile, SVFile

class DepParser(object):
    def __init__(self, dep_file):
        self.dep_file = dep_file

    def parse(self, dep_file):
        raise


class ParserFactory(object):
    def create(self, dep_file):
        import re
        from .vlog_parser import VerilogParser
        from .vhdl_parser import VHDLParser
        
        if isinstance(dep_file, VHDLFile) :
            return VHDLParser(dep_file)
        elif isinstance(dep_file, VerilogFile) or isinstance(dep_file,  SVFile) :
            vp = VerilogParser(dep_file)
            for d in dep_file.include_paths:
                vp.add_search_path(d)
            return vp
        else :
            raise ValueError("Unrecognized file format : %s" % dep_file.file_path)


def solve(fileset, top_entity):

    try:
        import networkx as nx
        import numpy as np
        import colorsys
    except Exception as e:
        logging.error(e)
        quit()
    hierarchy = nx.DiGraph()
    color_index = 0


    from .srcfile import SourceFileSet
    from .dep_file import DepRelation
    assert isinstance(fileset, SourceFileSet)
    fset = fileset.filter(DepFile)
    not_satisfied = 0
    logging.debug("PARSE BEGIN: Here, we will parse all the files in the fileset: no parsing should be done beyond this point")
    for investigated_file in fset:
        logging.debug("INVESTIGATED FILE: %s" % investigated_file)
        investigated_file.parse_if_needed()
    logging.debug("PARSE END: now the parsing is done")

    
    logging.info("Solve the file hierarchy from top module: %s" % top_entity)

    # Create a directed graph with all of the relations

    hierarchy_dict = {}

    for investigated_file in fset:

        logging.debug("investigated_file: %s" % investigated_file.path)

        if isinstance(investigated_file, VHDLFile) :

            # Do this file use a package? If so, we will consider that
            # all of the entities and architectures provided in the file
            # depend on the use packages.

            for entity_test in investigated_file.provided_entities:
                hierarchy.add_node(entity_test, node_color='r')
                hierarchy_dict[entity_test] = investigated_file
                for used_package in investigated_file.used_packages:
                    hierarchy.add_edge(entity_test, used_package[1])

            for architecture_test in investigated_file.provided_architectures:
                architecture_id = "%s(%s)" % (architecture_test.model[1], architecture_test.model[0])
                hierarchy.add_node(architecture_id)
                hierarchy_dict[architecture_id] = investigated_file
                hierarchy.add_edge(architecture_test.model[1], architecture_id)
                if architecture_test.entities:
                    for used_entity in architecture_test.entities:
                        hierarchy.add_edge(architecture_id, used_entity[1])
                if architecture_test.components:
                    for used_component in architecture_test.components:
                        hierarchy.add_edge(architecture_id, used_component)
                if architecture_test.instances:
                    for used_instance in architecture_test.instances:
                        hierarchy.add_edge(architecture_id, used_instance)
                for used_package in investigated_file.used_packages:
                    hierarchy.add_edge(architecture_id, used_package[1])


            for package_test in investigated_file.provided_packages:
                hierarchy.add_node(package_test.model)
                hierarchy_dict[package_test.model] = investigated_file
                #if package_test.components:
                #    for used_component in package_test.components:
                #        #hierarchy.add_edge(used_entity[1], architecture_test.model)
                #        hierarchy.add_edge(package_test.model, used_component)
                #        print(used_component)


        if isinstance(investigated_file, VerilogFile) :
            # In verilog world, packages are related with SystemVerilog
            for module_test in investigated_file.provided_modules:
                hierarchy.add_node(module_test.model)
                hierarchy_dict[module_test.model] = investigated_file
                if module_test.instances:
                    for used_instance in module_test.instances:
                        hierarchy.add_edge(module_test.model, used_instance[0])

    tree = nx.bfs_tree(hierarchy, top_entity)

    top_hierarchy = tree
    sorted_components= nx.topological_sort(top_hierarchy)

    # This should be reviewed: which is the order for the repeated files?
    # - Option A: If file exists, keep the old one and don't add the new file
    # - Option B: If file exists, delete the old position and add it to the end.
    solved_files = []
    for component in sorted_components:
        if component in hierarchy_dict:
            if not (hierarchy_dict[component] in solved_files):
                solved_files.append(hierarchy_dict[component])

    logging.info("Dependencies solved: %s files added to the hierarchy" % len(solved_files))


    logging.debug("SOLVE END")
    return (hierarchy, hierarchy_dict, top_hierarchy, solved_files)


def make_dependency_sorted_list(fileset, purge_unused=True, reverse=False):
    """Sort files in order of dependency. 
    Files with no dependencies first. 
    All files that another depends on will be earlier in the list."""
    dependable = [f for f in fileset if isinstance(f, DepFile)]
    non_dependable = [f for f in fileset if not isinstance(f, DepFile)]
    dependable.sort(key=lambda f: f.file_path.lower()) # Not necessary, but will tend to group files more nicely in the output.
    dependable.sort(key=DepFile.get_dep_level)
    sorted_list = non_dependable + dependable
    if reverse:
        sorted_list = list(reversed(sorted_list))
    return sorted_list
 
