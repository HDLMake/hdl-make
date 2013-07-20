from __future__ import print_function
import logging
import os
from dependable_file import DependableFile
from action import Action
import dep_solver
from flow_altera import QuartusProject


class GenerateQuartusProject(Action):
    def run(self):
        if self.env["quartus_path"] is None:
            logging.error("Can't generate a Quartus project. Quartus not found.")
            quit()
        else:
            logging.info("Generating/updating Quartus project.")

        self._check_all_fetched_or_quit()

        if os.path.exists(self.top_module.syn_project) or os.path.exists(self.top_module.syn_project + ".qsf"):
            self._update_existing_quartus_project()
        else:
            self._create_new_quartus_project()

    def _create_new_quartus_project(self):
        top_mod = self.modules_pool.get_top_module()
        fileset = self.modules_pool.build_global_file_list()
        non_dependable = fileset.inversed_filter(DependableFile)
        fileset = dep_solver.solve(fileset)
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
        non_dependable = fileset.inversed_filter(DependableFile)
        fileset = dep_solver.solve(fileset)
        fileset.add(non_dependable)
        prj = QuartusProject(top_mod.syn_project)
        prj.read()
        prj.preflow = None
        prj.postflow = None
        prj.add_files(fileset)
        prj.emit()
