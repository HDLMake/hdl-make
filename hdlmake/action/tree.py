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

from .action import Action
from hdlmake.util import path

import logging

class Tree(Action):
    def run(self):
        try:
            import networkx as nx
            import numpy as np
            import colorsys
        except Exception as e:
            logging.error(e)
            quit()

        self.modules_pool.build_file_set()
        hierarchy = self.modules_pool.hierarchy_tree
        top_id = self.modules_pool.top_module.top_module
        # Define the program used to write the graphviz:
        # Program should be one of: 
        #     twopi, gvcolor, wc, ccomps, tred, sccmap, fdp, 
        #     circo, neato, acyclic, nop, gvpr, dot, sfdp.
        if self.options.graphviz:
            import matplotlib.pyplot as plt
            pos=nx.graphviz_layout(hierarchy, prog=self.options.graphviz, root=top_id)
            nx.draw(hierarchy, pos,
                with_labels=True,
                alpha=0.5,
                node_size=100)
            plt.savefig("hierarchy.png")
            plt.show()


        #pos=nx.spring_layout(hierarchy)
        #colors=range(len(self.modules_pool))
        #nx.draw(hierarchy,pos,node_color=colors,width=4,edge_cmap=plt.cm.Blues)
        #print(hierarchy)
        #print(top_id)
        if self.options.web:
            import json
            from networkx.readwrite import json_graph
            data = json_graph.tree_data(hierarchy, root=top_id)
            #data = json_graph.tree_data(hierarchy, root='../../ip_cores/gn4124-core')
            #print(data)
            s = json.dumps(data)
            #print(s)

            json_file = open("hierarchy.json", "w")
            json_file.write(s)
            json_file.close()



