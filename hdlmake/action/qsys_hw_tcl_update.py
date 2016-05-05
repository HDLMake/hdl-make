#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 AUT
# Author: William Kamp (william.kamp@aut.ac.nz)
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
import hdlmake.new_dep_solver as dep_solver
import os
import shutil
import logging


class QsysHwTclUpdate(Action):
    def run(self):
        file_set = self.modules_pool.build_file_set()
        file_list = dep_solver.make_dependency_sorted_list(file_set)
        files_str = [os.path.relpath(f.path) for f in file_list]
        
        file_tcl = []
        for fs in files_str:
            path, fname = os.path.split(fs)
            file_tcl.append("add_fileset_file %s VHDL PATH %s" % (fname, fs))

        # mark the last file as the top level file. 
        file_tcl[-1] += " TOP_LEVEL_FILE"
        file_tcl.append("\n")
        
        hw_tcl_filename = self.modules_pool.get_top_module().hw_tcl_filename;

        infile = open(hw_tcl_filename,"r")
        inserted = True
        out_lines = []
        for line in infile.readlines():
            if line.startswith("add_fileset QUARTUS_SYNTH"):
                inserted = False
            if line.startswith("add_fileset SIM_VHDL"):
                inserted = False
            if line.startswith("add_fileset_file"):
                if not inserted:
                    out_lines.append("\n".join(file_tcl))
                    inserted = True
            else:
                out_lines.append(line)

        infile.close()

        hw_tcl_filename_backup = hw_tcl_filename + ".bak"
        shutil.copy2(hw_tcl_filename, hw_tcl_filename_backup)
        logging.info("Old hw.tcl file backed up to %s", hw_tcl_filename_backup)

        logging.info("Updating the file list in %s", hw_tcl_filename)
        
        
        outfile = open(hw_tcl_filename, "w")
        outfile.writelines(out_lines)
        outfile.close()
