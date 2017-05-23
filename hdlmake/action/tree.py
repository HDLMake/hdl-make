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


class ActionTree(Action):

    """Class providing methods to create a graph from pool and to analyze it"""

    def __init__(self, *args):
        super(ActionTree, self).__init__(*args)

    def _generate_tree_web(self, hierarchy, top_id):
        """Create a JSON file containing the graph hierarchy from pool"""
        if self.options.web:
            try:
                import json
                from networkx.readwrite import json_graph
            except ImportError as error_import:
                logging.error(error_import)
                quit()
            data = json_graph.tree_data(hierarchy, root=top_id)
            json_string = json.dumps(data)
            json_file = open("hierarchy.json", "w")
            json_file.write(json_string)
            json_file.close()

    def _generate_tree_graphviz(self, hierarchy, top_id):
        """Define the program used to write the graphviz:
        Program should be one of:
             twopi, gvcolor, wc, ccomps, tred, sccmap, fdp,
             circo, neato, acyclic, nop, gvpr, dot, sfdp
        """
        if self.options.graphviz:
            try:
                import matplotlib.pyplot as plt
                import networkx as nx
            except ImportError as error_import:
                logging.error(error_import)
                quit()
            pos = nx.graphviz_layout(hierarchy,
                                     prog=self.options.graphviz,
                                     root=top_id)
            nx.draw(hierarchy, pos,
                    with_labels=True,
                    alpha=0.5,
                    node_size=100)
            plt.savefig("hierarchy.png")
            plt.show()

    def generate_tree(self):
        """Generate the graph from pool and create the requested outcomes"""
        try:
            import networkx as nx
        except ImportError as error_import:
            logging.error(error_import)
            quit()
        unfetched_modules = False
        hierarchy = nx.DiGraph()

        if self.options.solved:
            logging.warning("This is the solved tree")
        else:
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
                    if self.options.withfiles:
                        if len(mod_aux.files):
                            for file_aux in mod_aux.files:
                                hierarchy.add_edge(mod_aux.path,
                                                   path.relpath(file_aux.path))

        if unfetched_modules:
            logging.warning("Some of the modules have not been fetched!")

        self._generate_tree_web(hierarchy, top_id)
        self._generate_tree_graphviz(hierarchy, top_id)
