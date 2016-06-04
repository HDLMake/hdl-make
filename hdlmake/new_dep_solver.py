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
    #print(fileset)
    #print(fset)
    not_satisfied = 0
    logging.debug("PARSE BEGIN: Here, we will parse all the files in the fileset: no parsing should be done beyond this point")
    for investigated_file in fset:
        logging.debug("INVESTIGATED FILE: %s" % investigated_file)
        investigated_file.parse_if_needed()
    logging.debug("PARSE END: now the parsing is done")

    
    logging.debug("SOLVE BEGIN")
    print("Search for the file providing top_entity and their architectures: %s" % top_entity)

    # Create a directed graph with all of the relations
    # 1- Search top entity
    # 2- Search architectures for top entity
    # 3- Search for components/entities

    #hierarchy.add_node(path.relpath(m.path))
    #hierarchy.add_node(m)
    #hierarchy.add_edge(path.relpath(m.parent.path), path.relpath(m.path))

    hierarchy_dict = {}

    for investigated_file in fset:

        print("investigated_file: %s" % investigated_file.path)

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
                hierarchy.add_node(architecture_test.model)
                hierarchy_dict[architecture_test.model] = investigated_file
                #hierarchy.add_edge(architecture_test.model, architecture_test.model[1])
                hierarchy.add_edge(architecture_test.model[1], architecture_test.model)
                if architecture_test.entities:
                    for used_entity in architecture_test.entities:
                        #hierarchy.add_edge(used_entity[1], architecture_test.model)
                        hierarchy.add_edge(architecture_test.model, used_entity[1])
                if architecture_test.components:
                    for used_component in architecture_test.components:
                        #hierarchy.add_edge(used_entity[1], architecture_test.model)
                        hierarchy.add_edge(architecture_test.model, used_component)
                if architecture_test.instances:
                    for used_instance in architecture_test.instances:
                        #hierarchy.add_edge(used_entity[1], architecture_test.model)
                        hierarchy.add_edge(architecture_test.model, used_instance)
                for used_package in investigated_file.used_packages:
                    hierarchy.add_edge(architecture_test.model, used_package[1])


            for package_test in investigated_file.provided_packages:
                hierarchy.add_node(package_test.model)
                hierarchy_dict[package_test] = investigated_file
                if package_test.components:
                    for used_component in package_test.components:
                        #hierarchy.add_edge(used_entity[1], architecture_test.model)
                        hierarchy.add_edge(package_test.model, used_component)
                        print(used_component)


            print("These are the dependency parameters for a VHDL file")
            print("Dump provided architectures from solver!")
            for architecture_test in investigated_file.provided_architectures:
                print("--------------------------")
                print("architecture_test.model")
                print(architecture_test.model)
                print("architecture_test.components")
                print(architecture_test.components)
                print("architecture_test.entities")
                print(architecture_test.entities)
                print("architecture_test.instances")
                print(architecture_test.instances)
                print("--------------------------")

            print("Dump provided entities from solver!")
            for entity_test in investigated_file.provided_entities:
                print("--------------------------")
                print(entity_test)
                if entity_test == top_entity: 
                    print("************* Hit!!!! **************")
                    print(investigated_file)
                print("--------------------------")

            print("Dump provided packages from solver!")
            for provided_package_test in investigated_file.provided_packages:
                print("--------------------------")
                print(provided_package_test)
                print("--------------------------")

            print("Dump used packages from solver!")
            for used_package_test in investigated_file.used_packages:
                print("--------------------------")
                print(used_package_test)
                print("--------------------------")


        if isinstance(investigated_file, VerilogFile) :
            # In verilog world, packages are related with SystemVerilog

            for module_test in investigated_file.provided_modules:
                hierarchy.add_node(module_test.model)
                hierarchy_dict[module_test.model] = investigated_file
                if module_test.instances:
                    for used_instance in module_test.instances:
                        #hierarchy.add_edge(used_entity[1], architecture_test.model)
                        hierarchy.add_edge(module_test.model, used_instance[0])


    #filelists = [nx.topological_sort(H) for H in nx.weakly_connected_component_subgraphs(hierarchy)]
    print("These are the filelists:")
    print("************************************")
    #for H in nx.weakly_connected_component_subgraphs(hierarchy):
    #for H in nx.strongly_connected_component_subgraphs(hierarchy):
    #    if top_entity in H:
    #        # This is our subgraph!
    #        top_hierarchy = H
    #        sorted_components= nx.topological_sort(H)
    #        print(sorted_components)
    #print("************************************")
    #print(hierarchy_dict)

    tree = nx.bfs_tree(hierarchy, top_entity)

    top_hierarchy = tree
    sorted_components= nx.topological_sort(top_hierarchy)
    print(sorted_components)

    print("FILES:")
    solved_files = []
    for component in sorted_components:
        if component in hierarchy_dict:
            if not (hierarchy_dict[component] in solved_files):
                solved_files.append(hierarchy_dict[component])
    #print(solved_files)
    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print("total files: %s" % len(solved_files))
    for file_test in solved_files:
        print(file_test.path)
    print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")

        # Define the program used to write the graphviz:
        # Program should be one of: 
        #     twopi, gvcolor, wc, ccomps, tred, sccmap, fdp, 
        #     circo, neato, acyclic, nop, gvpr, dot, sfdp.
    if True:
        import matplotlib.pyplot as plt
        pos=nx.graphviz_layout(top_hierarchy, prog='neato', root=top_entity)
        nx.draw(top_hierarchy, pos,
            with_labels=True,
            alpha=0.5,
            node_size=100)
        plt.savefig("hierarchy.png")
        plt.show()

    if False:
        import matplotlib.pyplot as plt
        pos=nx.graphviz_layout(hierarchy, prog='neato', root=top_entity)
        nx.draw(hierarchy, pos,
            with_labels=True,
            alpha=0.5,
            node_size=100)
        plt.savefig("hierarchy.png")
        plt.show()

    if False:
        import matplotlib.pyplot as plt
        hierarchy_u = hierarchy.to_undirected()
        #hierarchy_u = hierarchy
        pos=nx.graphviz_layout(hierarchy_u,prog="neato")
        for h in nx.connected_component_subgraphs(hierarchy_u):
            if top_entity in h:
                sortedfiles = nx.topological_sort(h)
                print("***********************")
                print(sortedfiles)
                print("***********************")
                nx.draw(h,pos,node_color='red')
            #else:
            #    nx.draw(h,pos,node_color='white')
        plt.show()


    if True:
        import json
        from networkx.readwrite import json_graph
        data = json_graph.tree_data(top_hierarchy, root=top_entity)
        #data = json_graph.tree_data(hierarchy, root='../../ip_cores/gn4124-core')
        #print(data)
        s = json.dumps(data)
        #print(s)
        json_file = open("hierarchy.json", "w")
        json_file.write(s)
        json_file.close()



    logging.debug("SOLVE END")
    return solved_files


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
    
def make_dependency_set(fileset, top_level_entity):
    logging.info("Create a set of all files required to build the named top_level_entity.")
    from srcfile import SourceFileSet
    from dep_file import DepRelation
    assert isinstance(fileset, SourceFileSet)
    fset = fileset.filter(DepFile)
    # Find the file that provides the named top level entity
    top_rel_vhdl = DepRelation("%s.%s" % ("work", top_level_entity), DepRelation.PROVIDE, DepRelation.ENTITY)
    top_rel_vlog = DepRelation("%s.%s" % ("work", top_level_entity), DepRelation.PROVIDE, DepRelation.MODULE)
    top_file = None
    logging.debug("Look for top level unit: %s." % top_level_entity)
    for chk_file in fset:
        for rel in chk_file.rels:
            if ((rel == top_rel_vhdl) or (rel == top_rel_vlog)):
                logging.debug("Found the top level file providing top level unit: %s." % chk_file)
                top_file = chk_file
                break;
        if top_file:
            break
    if top_file == None:
        logging.critical('Could not find a top level file that provides the top_module="%s". Continuing with the full file set.' % top_level_entity)
        return fileset
    # Collect only the files that the top level entity is dependant on, by walking the dependancy tree.
    try:
        dep_file_set = set()
        file_set = set([top_file])
        while True:
            chk_file = file_set.pop()
            dep_file_set.add(chk_file)
            file_set.update(chk_file.depends_on - dep_file_set)
    except KeyError:
        # no files left
        pass
    logging.info("Found %d files as dependancies of %s." % (len(dep_file_set), top_level_entity))
    #for dep_file in dep_file_set:
    #    logging.info("\t" + str(dep_file))
    return dep_file_set
