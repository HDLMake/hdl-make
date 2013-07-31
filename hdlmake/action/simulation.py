#!/usr/bin/env python
from __future__ import print_function
from action import Action
import logging
import dep_solver
import sys


class GenerateSimulationMakefile(Action):
    def _check_manifest(self):
        if not self.modules_pool.get_top_module().top_module:
            logging.error("top_module variable must be set in the top manifest.")
            sys.exit("Exiting")

    def run(self):
        self._check_all_fetched_or_quit()
        self._check_manifest()

        tm = self.modules_pool.top_module
        if tm.sim_tool == "iverilog":
            self._generate_iverilog_makefile()
        elif tm.sim_tool == "isim":
            self._generate_isim_makefile()
        elif tm.sim_tool == "vsim" or tm.sim_tool == "modelsim":
            self._generate_vsim_makefile()
        else:
            logging.error("Unrecognized or not specified simulation tool: %s" % str(tm.sim_tool))
            sys.exit("Exiting")

    def _generate_vsim_makefile(self):
#        p.info("Generating makefile for simulation.")
        if self.env["modelsim_path"] is None:
            logging.error("Can't generate a Modelsim makefile. Modelsim not found.")
            sys.exit("Exiting")
        else:
            logging.info("Generating ModelSim makefile for simulation.")

        pool = self.modules_pool
        top_module = pool.get_top_module()
        flist = pool.build_global_file_list()
        flist_sorted = dep_solver.solve(flist)
        self.make_writer.generate_vsim_makefile(flist_sorted, top_module)

    def _generate_isim_makefile(self):
#        p.info("Generating makefile for simulation.")
        if self.env["isim_path"] is None and self.env["xilinx"] is None:
            logging.error("Can't generate an ISim makefile. ISim not found.")
            sys.exit("Exiting")
        else:
            logging.info("Generating ISE Simulation (ISim) makefile for simulation.")

        pool = self.modules_pool
        top_module = pool.get_top_module()

        flist = pool.build_global_file_list()
        flist_sorted = dep_solver.solve(flist)
        self.make_writer.generate_isim_makefile(flist_sorted, top_module)

    def _generate_iverilog_makefile(self):
        if self.env["iverilog_path"] is None:
            logging.error("Can't generate an IVerilog makefile. IVerilog not found.")
            sys.exit("Exiting")
        else:
            logging.info("Generating IVerilog makefile for simulation.")

        pool = self.modules_pool

        tm = pool.get_top_module()
        flist = pool.build_global_file_list()
        flist_sorted = dep_solver.solve(flist)
        self.make_writer.generate_iverilog_makefile(flist_sorted, tm, pool)
