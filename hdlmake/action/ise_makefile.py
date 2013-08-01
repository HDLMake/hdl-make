from __future__ import print_function
from action import Action
import logging
import global_mod


class GenerateISEMakefile(Action):
    def run(self):
        import global_mod
        global_mod.mod_pool = self.modules_pool
        logging.info("Generating makefile for local synthesis.")

        ise_path = global_mod.env["ise_path"]

        global_mod.makefile_writer.generate_ise_makefile(top_mod=self.modules_pool.get_top_module(),
                                               ise_path=ise_path)
