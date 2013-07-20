
import logging
from action import Action


class FetchModules(Action):
    def run(self, unfetched_only=False):
        logging.info("Fetching needed modules.")
        self.modules_pool.fetch_all(unfetched_only)
        logging.debug(str(self.modules_pool))
