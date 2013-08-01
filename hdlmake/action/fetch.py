
import logging
import sys
from action import Action


class FetchModules(Action):
    def _check_options(self):
        if self.options.flatten is True and self.env["coredir"] is not None:
            logging.error("Options clash: --flatten and HDLMAKE_COREDIR set at a time\n"
                          "Take one out of the two")
            sys.exit("\nExiting")

    def run(self):
        logging.info("Fetching needed modules.")
        self.modules_pool.fetch_all(unfetched_only=not self.options.update, flatten=self.options.flatten)
        logging.debug(str(self.modules_pool))
