
import logging
import sys

from action import Action
from simulation import GenerateSimulationMakefile
from ise_project import GenerateISEProject
from quartus_project import GenerateQuartusProject
from ise_makefile import GenerateISEMakefile
from remote_synthesis import GenerateRemoteSynthesisMakefile


class Default(Action):
    def run(self):
        self._check_manifest()
        tm = self.top_module

        if not self.modules_pool.is_everything_fetched():
            self.fetch(unfetched_only=True)

        if tm.action == "simulation":
            simulation_makefile = SimulationMakefile(modules_pool=self.modules_pool, options=self.options, env=self.env)
            simulation_makefile.run()

        elif tm.action == "synthesis":

            if tm.target == "xilinx":
                ise_project = ISEProject(modules_pool=self.modules_pool, options=self.options, env=self.env)
                ise_project.run()

                ise_makefile = ISEProject(modules_pool=self.modules_pool, options=self.options, env=self.env)
                ise_makefile.run()

                remote_synthesis = ISEProject(modules_pool=self.modules_pool, options=self.options, env=self.env)
                remote_synthesis.run()
            elif tm.target == "altera":
                quartus_project = QuartusProject(modules_pool=self.modules_pool, options=self.options, env=self.env)
                quartus_project.run()
            else:
                logging.error("Unrecognized target: %s" % tm.target)
                sys.exit("Exiting")

    def _check_manifest(self):
        if self.top_module.action != "simulation" and self.top_module.action != "synthesis":
            logging.error("'action' variable must be defined in the top manifest\n"
                          "Allowed values are: \"simulation\" or \"synthesis\"\n"
                          "This variable in a manifest file is necessary for Hdlmake\n"
                          "to be able to know what to do with the given modules' structure.\n"
                          "For more help type `hdlmake --help'\n"
                          "or visit http://www.ohwr.org/projects/hdl-make")
            sys.exit("Exiting")

        if self.top_module.syn_project is None:
            logging.error("syn_project variable must be defined in the manifest")
            sys.exit("Exiting")
