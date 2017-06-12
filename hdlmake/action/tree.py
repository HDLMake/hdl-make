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

"""Module providing graph funtionalities to HDLMake"""

from __future__ import absolute_import
from hdlmake.util import path

import logging

from .action import Action
from hdlmake.dep_file import DepFile


class ActionTree(Action):

    """Class providing methods to create a graph from pool and to analyze it"""

    def __init__(self, *args):
        super(ActionTree, self).__init__(*args)

    def _generate_tree_web(self, hierarchy, top_id):
        """Create a JSON file containing the graph hierarchy from pool"""
        try:
            import json
            import networkx as nx
            from networkx.readwrite import json_graph
        except ImportError as error_import:
            logging.error(error_import)
            quit()
        if self.options.mode == 'dfs':
            hierarchy = nx.dfs_tree(hierarchy, top_id)
        elif self.options.mode == 'bfs':
            hierarchy = nx.bfs_tree(hierarchy, top_id, reverse=False)
        data = json_graph.tree_data(hierarchy, root=top_id)
        json_string = json.dumps(data)
        json_file = open("hierarchy.json", "w")
        json_file.write(json_string)
        json_file.close()

    def generate_tree(self):
        """Generate the graph from pool and create the requested outcomes"""
        try:
            import networkx as nx
        except ImportError as error_import:
            logging.error(error_import)
            quit()
        unfetched_modules = False
        hierarchy = nx.DiGraph()

        if self.options.mode == "mods":
            for mod_aux in self:
                if not mod_aux.isfetched:
                    unfetched_modules = True
                else:
                    if mod_aux.parent:
                        hierarchy.add_node(mod_aux.path)
                        hierarchy.add_edge(mod_aux.parent.path, mod_aux.path)
                    else:
                        hierarchy.add_node(mod_aux.path)
                        top_id = mod_aux.path
                    if len(mod_aux.files):
                        for file_aux in mod_aux.files:
                            hierarchy.add_edge(mod_aux.path,
                                               path.relpath(file_aux.path))
        elif (self.options.mode == 'dfs' or
              self.options.mode == 'bfs'):


            logging.warning("This is the solved tree")
            #self.top_entity = self.options.top
            self.build_file_set()
            self.solve_file_set()

            from hdlmake.srcfile import SourceFileSet
            from hdlmake.dep_file import DepRelation
            assert isinstance(self.parseable_fileset, SourceFileSet)
            fset = self.parseable_fileset.filter(DepFile)
            # Find the file that provides the named top level entity
            top_rel_vhdl = DepRelation(
                "%s.%s" %
                ("work", self.top_entity), DepRelation.PROVIDE, DepRelation.ENTITY)
            top_rel_vlog = DepRelation(
                "%s.%s" %
                ("work", self.top_entity), DepRelation.PROVIDE, DepRelation.MODULE)
            top_file = None
            for chk_file in fset:
                hierarchy.add_node(path.relpath(chk_file.path))
                for file_required in chk_file.depends_on:
                    hierarchy.add_edge(path.relpath(chk_file.path), path.relpath(file_required.path))
                for rel in chk_file.rels:
                    if (rel == top_rel_vhdl) or (rel == top_rel_vlog):
                        top_file = chk_file
                        top_id = path.relpath(chk_file.path)
            if top_file is None:
                logging.critical('Could not find a top level file that provides the '
                                 'top_module="%s". Continuing with the full file set.',
                                 top_level_entity)

        else:
            logging.error('Unknown tree mode: %s', self.options.mode)
            quit()

        if unfetched_modules:
            logging.warning("Some of the modules have not been fetched!")

        self._generate_tree_web(hierarchy, top_id)
