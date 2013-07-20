from __future__ import print_function
import logging
from action import Action
import sys
import os
from dependable_file import DependableFile
import dep_solver
from srcfile import SourceFileSet
from flow import ISEProject
from srcfile import SourceFileFactory


class GenerateISEProject(Action):
    def run(self):
        env = self.env
        if self.env["ise_path"] is None:
            logging.error("Can't generate an ISE project. ISE not found.")
            quit()
        else:
            if not env["ise_version"]:
                logging.error("Xilinx version cannot be deduced. Cannot generate ISE "
                              "project file properly. Please use syn_ise_version in the manifest "
                              "or set")
                sys.exit("Exiting")
            else:
                logging.info("Generating project for ISE v. %d.%d" % (env["ise_version"][0], env["ise_version"][1]))
        self._check_all_fetched_or_quit()

        if os.path.exists(self.top_module.syn_project) or os.path.exists(self.top_module.syn_project + ".xise"):
            self._handle_ise_project(update=True)
        else:
            self._handle_ise_project(update=False)

    def _handle_ise_project(self, update=False):
        top_mod = self.modules_pool.get_top_module()
        fileset = self.modules_pool.build_global_file_list()
        non_dependable = fileset.inversed_filter(DependableFile)
        dependable = dep_solver.solve(fileset)
        all_files = SourceFileSet()
        all_files.add(non_dependable)
        all_files.add(dependable)

        prj = ISEProject(ise=self.env["ise_version"],
                         top_mod=self.modules_pool.get_top_module())
        prj.add_files(all_files)
        sff = SourceFileFactory()
        logging.debug(top_mod.vlog_opt)
        prj.add_files([sff.new(top_mod.vlog_opt)])
        prj.add_libs(all_files.get_libs())
        if update is True:
            prj.load_xml(top_mod.syn_project)
        else:
            prj.add_initial_properties(syn_device=top_mod.syn_device,
                                       syn_grade=top_mod.syn_grade,
                                       syn_package=top_mod.syn_package,
                                       syn_top=top_mod.syn_top)
        prj.emit_xml(top_mod.syn_project)
