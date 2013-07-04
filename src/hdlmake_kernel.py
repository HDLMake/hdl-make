#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 CERN
# Author: Pawel Szostek (pawel.szostek@cern.ch)
# Modified to allow ISim simulation by Lucas Russo (lucas.russo@lnls.br)
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

import os
import logging
import path
from makefile_writer import MakefileWriter
from flow import ISEProject
from flow_altera import QuartusProject
from dep_solver import DependencySolver
from srcfile import IDependable, SourceFileSet, SourceFileFactory


class HdlmakeKernel(object):
    def __init__(self, modules_pool, connection, options):
        self.modules_pool = modules_pool
        self.connection = connection
        self.make_writer = MakefileWriter("Makefile")
        self.options = options

    @property
    def top_module(self):
        return self.modules_pool.get_top_module()

    def run(self):
        tm = self.top_module

        if not self.modules_pool.is_everything_fetched():
            self.fetch(unfetched_only=True)

        if tm.action == "simulation":
            self.generate_simulation_makefile()
        elif tm.action == "synthesis":
            if tm.syn_project is None:
                logging.error("syn_project variable must be defined in the manifest")
                quit()
            if tm.target.lower() == "xilinx":
                self.generate_ise_project()
                self.generate_ise_makefile()
                self.generate_remote_synthesis_makefile()
            elif tm.target.lower() == "altera":
                self.generate_quartus_project()
              # self.generate_quartus_makefile()
              # self.generate_quartus_remote_synthesis_makefile()
            else:
                raise RuntimeError("Unrecognized target: "+tm.target)
        else:
            logging.error("'action' variable must be defined in the top manifest\n"
                          "Allowed values are: \"simulation\" or \"synthesis\"\n"
                          "This variable in a manifest file is necessary for Hdlmake\n"
                          "to be able to know what to do with the given modules' structure.\n"
                          "For more help type `hdlmake --help'\n"
                          "or visit http://www.ohwr.org/projects/hdl-make")
            quit()

    def list_modules(self):
        for m in self.modules_pool:
            if not m.isfetched:
                print("#!UNFETCHED")
                print(m.url+'\n')
            else:
                print(path.relpath(m.path))
                if m.source in ["svn", "git"]:
                    print("#"+m.url)
                if not len(m.files):
                    print("   # no files")
                else:
                    for f in m.files:
                        print("   " + path.relpath(f.path, m.path))
                print("")

    def list_files(self):
        files_str = []
        for m in self.modules_pool:
            if not m.isfetched:
                continue
            files_str.append(" ".join([f.path for f in m.files]))
        print(" ".join(files_str))

    def fetch(self, unfetched_only=False):
        logging.info("Fetching needed modules.")
        self.modules_pool.fetch_all(unfetched_only)
        logging.debug(str(self.modules_pool))

    def generate_simulation_makefile(self):
        tm = self.modules_pool.top_module
        if tm.sim_tool == "iverilog":
            self._generate_iverilog_makefile()
        elif tm.sim_tool == "isim":
            self._generate_isim_makefile()
        elif tm.sim_tool == "vsim" or tm.sim_tool == "modelsim":
            self._generate_vsim_makefile()
        else:
            raise RuntimeError("Unrecognized or not specified simulation tool: %s" % str(tm.sim_tool))
            quit()

    def _check_all_fetched_or_quit(self):
        pool = self.modules_pool
        if not pool.is_everything_fetched():
            logging.error("A module remains unfetched. "
                          "Fetching must be done prior to makefile generation")
            print(str([str(m) for m in self.modules_pool.modules if not m.isfetched]))
            quit()

    def _generate_vsim_makefile(self):
#        p.info("Generating makefile for simulation.")
        logging.info("Generating ModelSim makefile for simulation.")
        solver = DependencySolver()

        pool = self.modules_pool
        self._check_all_fetched_or_quit()
        top_module = pool.get_top_module()
        flist = pool.build_global_file_list()
        flist_sorted = solver.solve(flist)
        #self.make_writer.generate_modelsim_makefile(flist_sorted, top_module)
        self.make_writer.generate_vsim_makefile(flist_sorted, top_module)

    def _generate_isim_makefile(self):
#        p.info("Generating makefile for simulation.")
        logging.info("Generating ISE Simulation (ISim) makefile for simulation.")
        solver = DependencySolver()

        pool = self.modules_pool
        self._check_all_fetched_or_quit()
        top_module = pool.get_top_module()

        if not top_module.top_module:
            logging.error("top_module variable must be set in the top manifest.")
            quit()
        flist = pool.build_global_file_list()
        flist_sorted = solver.solve(flist)
        self.make_writer.generate_isim_makefile(flist_sorted, top_module)

    def _generate_iverilog_makefile(self):
        from dep_solver import DependencySolver
        logging.info("Generating makefile for simulation.")
        solver = DependencySolver()
        pool = self.modules_pool

        self._check_all_fetched_or_quit()
        tm = pool.get_top_module()
        flist = pool.build_global_file_list()
        flist_sorted = solver.solve(flist)
        self.make_writer.generate_iverilog_makefile(flist_sorted, tm, pool)

    def generate_ise_makefile(self):
        import global_mod
        global_mod.mod_pool = self.modules_pool
        logging.info("Generating makefile for local synthesis.")

        ise_path = self.__figure_out_ise_path()

        self.make_writer.generate_ise_makefile(top_mod=self.modules_pool.get_top_module(), ise_path=ise_path)

    def generate_remote_synthesis_makefile(self):
        if self.connection.ssh_user is None or self.connection.ssh_server is None:
            logging.warning("Connection data is not given. "
                            "Accessing environmental variables in the makefile")
        logging.info("Generating makefile for remote synthesis.")

        top_mod = self.modules_pool.get_top_module()
        if not os.path.exists(top_mod.fetchto):
            logging.warning("There are no modules fetched. "
                            "Are you sure it's correct?")

        ise_path = self.__figure_out_ise_path()
        tcl = self.__search_tcl_file()

        if tcl is None:
            self.__generate_tcl()
            tcl = "run.tcl"
        files = self.modules_pool.build_very_global_file_list()

        sff = SourceFileFactory()
        files.add(sff.new(tcl))
        files.add(sff.new(top_mod.syn_project))

        self.make_writer.generate_remote_synthesis_makefile(files=files, name=top_mod.syn_name,
        cwd=os.getcwd(), user=self.connection.ssh_user, server=self.connection.ssh_server, ise_path=ise_path)

    def generate_ise_project(self):
        env = global_mod.env
        logging.info("Generating/updating ISE project")
        self._check_all_fetched_or_quit()
        if not env["ise_version"]:
            logging.error("Xilinx version cannot be deduced. Cannot generate ISE "
                          "project file properly. Please use syn_ise_version in the manifest "
                          "or set")
            quit()
        else:
            logging.info("Generating project for ISE v. %d.%d" % (env["ise_version"][0], env["ise_version"][1]))

        if os.path.exists(self.top_module.syn_project):
            self._update_existing_ise_project()
        else:
            self._create_new_ise_project()

    def generate_quartus_project(self):
        logging.info("Generating/updating Quartus project.")

        self._check_all_fetched_or_quit()

        if os.path.exists(self.top_module.syn_project + ".qsf"):
            self._update_existing_quartus_project()
        else:
            self._create_new_quartus_project()

    def __is_xilinx_screwed(self):
        if self.__check_ise_version() is None:
            return True
        else:
            return False

    def _update_existing_ise_project(self):
        top_mod = self.modules_pool.get_top_module()
        fileset = self.modules_pool.build_global_file_list()
        solver = DependencySolver()
        non_dependable = fileset.inversed_filter(IDependable)
        dependable = solver.solve(fileset)
        all_files = SourceFileSet()
        all_files.add(non_dependable)
        all_files.add(dependable)

        prj = ISEProject(ise=global_mod.env["ise_version"],
                         top_mod=self.modules_pool.get_top_module())
        prj.add_files(all_files)
        from srcfile import SourceFileFactory
        sff = SourceFileFactory()
        logging.debug(top_mod.vlog_opt)
        prj.add_files([sff.new(top_mod.vlog_opt)])
        prj.add_libs(all_files.get_libs())
        prj.load_xml(top_mod.syn_project)
        prj.emit_xml(top_mod.syn_project)

    def _create_new_ise_project(self, ise):
        top_mod = self.modules_pool.get_top_module()
        fileset = self.modules_pool.build_global_file_list()
        solver = DependencySolver()
        non_dependable = fileset.inversed_filter(IDependable)
        fileset = solver.solve(fileset)
        fileset.add(non_dependable)

        prj = ISEProject(ise=global_mod.env["ise_version"],
                         top_mod=self.modules_pool.get_top_module())
        prj.add_files(fileset)
        prj.add_libs(fileset.get_libs())
        from srcfile import SourceFileFactory
        sff = SourceFileFactory()
        logging.debug(top_mod.vlog_opt)
        prj.add_files([sff.new(top_mod.vlog_opt)])
        prj.add_initial_properties(syn_device=top_mod.syn_device,
                                   syn_grade=top_mod.syn_grade,
                                   syn_package=top_mod.syn_package,
                                   syn_top=top_mod.syn_top)

        prj.emit_xml(top_mod.syn_project)

    def _create_new_quartus_project(self):
        top_mod = self.modules_pool.get_top_module()
        fileset = self.modules_pool.build_global_file_list()
        solver = DependencySolver()
        non_dependable = fileset.inversed_filter(IDependable)
        fileset = solver.solve(fileset)
        fileset.add(non_dependable)

        prj = QuartusProject(top_mod.syn_project)
        prj.add_files(fileset)

        prj.add_initial_properties(top_mod.syn_device,
                                   top_mod.syn_grade,
                                   top_mod.syn_package,
                                   top_mod.syn_top)
        prj.preflow = None
        prj.postflow = None

        prj.emit()

    def _update_existing_quartus_project(self):
        top_mod = self.modules_pool.get_top_module()
        fileset = self.modules_pool.build_global_file_list()
        solver = DependencySolver()
        non_dependable = fileset.inversed_filter(IDependable)
        fileset = solver.solve(fileset)
        fileset.add(non_dependable)
        prj = QuartusProject(top_mod.syn_project)
        prj.read()
        prj.preflow = None
        prj.postflow = None
        prj.add_files(fileset)
        prj.emit()

    def run_local_synthesis(self):
        tm = self.modules_pool.get_top_module()
        if tm.target == "xilinx":
            import global_mod
            global_mod.mod_pool = self.modules_pool
            if not os.path.exists("run.tcl"):
                self.__generate_tcl()
            os.system("xtclsh run.tcl")
        else:
            logging.error("Target " + tm.target + " is not synthesizable")

    def run_remote_synthesis(self):
        ssh = self.connection
        cwd = os.getcwd()

        logging.debug("The program will be using ssh connection: "+str(ssh))
        if not ssh.is_good():
            logging.error("SSH connection failure. Remote host doesn't response.")
            quit()

        if not os.path.exists(self.top_module.fetchto):
            logging.warning("There are no modules fetched. Are you sure it's correct?")

        files = self.modules_pool.build_very_global_file_list()
#        tcl = self.__search_tcl_file()
#        if tcl is None:
        self.__generate_tcl()
        tcl = "run.tcl"

        sff = SourceFileFactory()
        files.add(sff.new(tcl))
        files.add(sff.new(self.top_module.syn_project))

        dest_folder = ssh.transfer_files_forth(files,
            dest_folder=self.top_module.syn_name)
        syn_cmd = "cd "+dest_folder+cwd+" && xtclsh run.tcl"

        logging.debug("Launching synthesis on " + str(ssh) + ": " + syn_cmd)
        ret = ssh.system(syn_cmd)
        if ret == 1:
            logging.error("Synthesis failed. Nothing will be transfered back")
            quit()

        cur_dir = os.path.basename(cwd)
        os.chdir("..")
        ssh.transfer_files_back(what=dest_folder+cwd, where=".")
        os.chdir(cur_dir)

    def __search_tcl_file(self, directory=None):
        if directory is None:
            directory = "."
        filenames = os.listdir(directory)
        tcls = []
        for filename in filenames:
            file_parts = filename.split('.')
            if file_parts[len(file_parts)-1] == "tcl":
                tcls.append(filename)
        if len(tcls) == 0:
            return None
        if len(tcls) > 1:
            logging.error("Multiple tcls in the current directory!\n" + str(tcls))
            quit()
        return tcls[0]

    def __generate_tcl(self):
        f = open("run.tcl", "w")
        f.write("project open " + self.top_module.syn_project + '\n')
        f.write("process run {Generate Programming File} -force rerun_all\n")
        f.close()

    def clean_modules(self):
        logging.info("Removing fetched modules..")
        remove_list = [m for m in self.modules_pool if m.source in ["svn", "git"] and m.isfetched]
        remove_list.reverse()  # we will remove modules in backward order
        if len(remove_list):
            for m in remove_list:
                print("\t" + m.url + " [from: " + m.path + "]")
                m.remove_dir_from_disk()
        else:
            logging.info("There are no modules to be removed")

    def generate_fetch_makefile(self):
        pool = self.modules_pool

        if pool.get_fetchable_modules() == []:
            logging.error("There are no fetchable modules. "
                          "No fetch makefile is produced")
            quit()

        if not pool.is_everything_fetched():
            logging.error("A module remains unfetched. "
                          "Fetching must be done prior to makefile generation")
            quit()
        self.make_writer.generate_fetch_makefile(pool)

    def merge_cores(self):
        from srcfile import VerilogFile, VHDLFile, NGCFile
        from vlog_parser import VerilogPreprocessor

        solver = DependencySolver()

        pool = self.modules_pool
        if not pool.is_everything_fetched():
            logging.error("A module remains unfetched. Fetching must be done prior to makefile generation")
            print(str([str(m) for m in self.modules_pool.modules if not m.isfetched]))
            quit()

        flist = pool.build_global_file_list()
        flist_sorted = solver.solve(flist)
#        if not os.path.exists(self.options.merge_cores):
 #           os.makedirs(self.options.merge_cores)
        base = self.options.merge_cores

        f_out = open(base+".vhd", "w")
        f_out.write("\n\n\n\n")
        f_out.write("------------------------------ WARNING -------------------------------\n")
        f_out.write("-- This code has been generated by hdlmake --merge-cores option     --\n")
        f_out.write("-- It is provided for your convenience, to spare you from adding    --\n")
        f_out.write("-- lots of individual source files to ISE/Modelsim/Quartus projects --\n")
        f_out.write("-- mainly for Windows users. Please DO NOT MODIFY this file. If you --\n")
        f_out.write("-- need to change something inside, edit the original source file   --\n")
        f_out.write("-- and re-genrate the merged version!                               --\n")
        f_out.write("----------------------------------------------------------------------\n")
        f_out.write("\n\n\n\n")

        for vhdl in flist_sorted.filter(VHDLFile):
            f_out.write("\n\n--- File: %s ----\n\n" % vhdl.rel_path())
            f_out.write(open(vhdl.rel_path(), "r").read()+"\n\n")
                #print("VHDL: %s" % vhdl.rel_path())
        f_out.close()

        f_out = open(base+".v", "w")

        f_out.write("\n\n\n\n")
        f_out.write("////////////////////////////// WARNING ///////////////////////////////\n")
        f_out.write("// This code has been generated by hdlmake --merge-cores option     //\n")
        f_out.write("// It is provided for your convenience, to spare you from adding    //\n")
        f_out.write("// lots of individual source files to ISE/Modelsim/Quartus projects //\n")
        f_out.write("// mainly for Windows users. Please DO NOT MODIFY this file. If you //\n")
        f_out.write("// need to change something inside, edit the original source file   //\n")
        f_out.write("// and re-genrate the merged version!                               //\n")
        f_out.write("//////////////////////////////////////////////////////////////////////\n")
        f_out.write("\n\n\n\n")

        for vlog in flist_sorted.filter(VerilogFile):
            f_out.write("\n\n//    File: %s     \n\n" % vlog.rel_path())
            vpp = VerilogPreprocessor()
            vpp.add_path(vlog.dirname)
            f_out.write(vpp.preprocess(vlog.rel_path()))
        f_out.close()

        for ngc in flist_sorted.filter(NGCFile):
            import shutil
            print("NGC:%s " % ngc.rel_path())
            shutil.copy(ngc.rel_path(), self.options.merge_cores+"/")
