from action import Action
import logging


class GenerateFetchMakefile(Action):
    def run(self):
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
