from action import Action
import logging


class GenerateFetchMakefile(Action):
    def run(self):
        pool = self.modules_pool

        if pool.get_fetchable_modules() == []:
            logging.error("There are no fetchable modules. "
                          "No fetch makefile is produced")
            quit()

        self._check_all_fetched_or_quit()
        self.make_writer.generate_fetch_makefile(pool)
